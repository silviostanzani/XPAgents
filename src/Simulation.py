import os
import re
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Dict, Any, Optional

from pydantic import BaseModel, Field, ValidationError
from crewai import Agent, Task, Crew, Process, LLM
import json_repair

try:
    from src.createAgents import criar_agentes, criar_llm, carregar_gemini_api_key
    from src.KB import inicializar_base
except ImportError:
    from createAgents import criar_agentes, criar_llm, carregar_gemini_api_key
    from KB import inicializar_base

# Diretório base de execução (padrão: /home/silvio/XPAgents)
EXEC_DIR_PADRAO = Path(os.environ.get("XPAGENTS_WORK_DIR", "/home/silvio/XPAgents"))
BASE_KB_PADRAO = EXEC_DIR_PADRAO / "kb"
SAIDA_PADRAO = EXEC_DIR_PADRAO / "resultados"

# ---------- Saída estruturada da análise ----------
class AnaliseNegociacao(BaseModel):
    resultado: Literal["sucesso", "insucesso", "indefinido"] = "indefinido"
    confianca: int = Field(default=50, ge=0, le=100)
    justificativa: str = ""
    momento_decisivo: str = ""
    objecoes_cliente: List[str] = Field(default_factory=list)
    estrategias_que_funcionaram: List[str] = Field(default_factory=list)
    erros_da_empresa: List[str] = Field(default_factory=list)
    recomendacoes: List[str] = Field(default_factory=list)

# ---------- Carga da base de conhecimento ----------
def garantir_base(base_dir: Path) -> None:
    """Garante que a base de conhecimento existe no diretório informado."""
    if not base_dir.exists() or not (base_dir / "empresa").exists():
        inicializar_base(base_dir)

def listar_opcoes(base_dir: Path, categoria: str) -> List[str]:
    pasta = Path(base_dir) / categoria
    if not pasta.exists():
        return []
    return sorted(p.stem for p in pasta.iterdir() if p.is_file())

def carregar_item(base_dir: Path, categoria: str, nome: str) -> str:
    """nome = arquivo sem extensão; '*' concatena todos os arquivos da pasta."""
    garantir_base(base_dir)
    pasta = Path(base_dir) / categoria
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {pasta}")
    if nome == "*":
        arquivos = sorted(p for p in pasta.iterdir() if p.is_file())
        return "\n\n".join(p.read_text(encoding="utf-8") for p in arquivos)
    for p in pasta.iterdir():
        if p.is_file() and p.stem == nome:
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"'{nome}' não existe em {categoria}/. Opções: {listar_opcoes(base_dir, categoria)}"
    )

def detectar_iniciador(texto_contato: str, padrao: str = "empresa") -> str:
    m = re.search(r"^iniciador:\s*(empresa|cliente)", texto_contato, re.I | re.M)
    return m.group(1).lower() if m else padrao

# ---------- Um turno de fala ----------
MARCADOR_FIM = "[FIM]"

def _limpar(texto: str) -> str:
    texto = texto.strip().strip('"').strip()
    texto = re.sub(
        r"^\s*(\*\*)?(empresa|cliente|representante|vendedor)(\*\*)?\s*:\s*",
        "",
        texto,
        flags=re.I,
    )
    return texto.strip()

def _formatar(mensagens: List[Dict[str, Any]]) -> str:
    return "\n".join(f"{m['autor'].upper()}: {m['texto']}" for m in mensagens)

def _falar(agente: Agent, quem: str, historico: str, primeira_fala: bool, cfg: Dict[str, Any], ultima_rodada: bool) -> str:
    if primeira_fala:
        instrucao = "A conversa ainda não começou. Escreva a mensagem de abertura, coerente com a natureza do contato."
    else:
        instrucao = "Escreva a sua próxima mensagem, respondendo ao que foi dito por último."
    extra = ""
    if cfg.get("encerramento_antecipado", True):
        extra = (
            f"\nSe a conversa já chegou a um desfecho claro (fechamento, recusa definitiva ou pedido de "
            f"encerramento), termine a mensagem com {MARCADOR_FIM}."
        )
    if ultima_rodada:
        extra += "\nEsta é a última rodada permitida: encaminhe a conversa para um desfecho (aceite, recusa ou próximo passo claro)."

    task = Task(
        description=f"""HISTÓRICO DA CONVERSA ATÉ AGORA:
{historico if historico else '(vazio)'}

{instrucao}{extra}
Escreva APENAS o texto da mensagem de {quem}, sem prefixos como "Empresa:" ou "Cliente:".""",
        expected_output=f"Uma única mensagem de {quem}, em texto corrido.",
        agent=agente,
    )
    crew = Crew(agents=[agente], tasks=[task], process=Process.sequential, verbose=False)
    return str(crew.kickoff().raw)

async def _falar_async(agente: Agent, quem: str, historico: str, primeira_fala: bool, cfg: Dict[str, Any], ultima_rodada: bool) -> str:
    if primeira_fala:
        instrucao = "A conversa ainda não começou. Escreva a mensagem de abertura, coerente com a natureza do contato."
    else:
        instrucao = "Escreva a sua próxima mensagem, respondendo ao que foi dito por último."
    extra = ""
    if cfg.get("encerramento_antecipado", True):
        extra = (
            f"\nSe a conversa já chegou a um desfecho claro (fechamento, recusa definitiva ou pedido de "
            f"encerramento), termine a mensagem com {MARCADOR_FIM}."
        )
    if ultima_rodada:
        extra += "\nEsta é a última rodada permitida: encaminhe a conversa para um desfecho (aceite, recusa ou próximo passo claro)."

    task = Task(
        description=f"""HISTÓRICO DA CONVERSA ATÉ AGORA:
{historico if historico else '(vazio)'}

{instrucao}{extra}
Escreva APENAS o texto da mensagem de {quem}, sem prefixos como "Empresa:" ou "Cliente:".""",
        expected_output=f"Uma única mensagem de {quem}, em texto corrido.",
        agent=agente,
    )
    crew = Crew(agents=[agente], tasks=[task], process=Process.sequential, verbose=False)
    saida = await crew.kickoff_async()
    return str(saida.raw)

# ---------- Análise final (JSON validado, com retentativas) ----------
SCHEMA_JSON = """{
  "resultado": "sucesso" | "insucesso" | "indefinido",
  "confianca": <inteiro de 0 a 100>,
  "justificativa": "<texto>",
  "momento_decisivo": "<texto>",
  "objecoes_cliente": ["<texto>", ...],
  "estrategias_que_funcionaram": ["<texto>", ...],
  "erros_da_empresa": ["<texto>", ...],
  "recomendacoes": ["<texto>", ...]
}"""

def _extrair_json(texto: str) -> Dict[str, Any]:
    texto_limpo = re.sub(r"```(?:json)?", "", texto)
    ini, fim = texto_limpo.find("{"), texto_limpo.rfind("}")
    if ini != -1 and fim != -1:
        bloco = texto_limpo[ini:fim + 1]
        try:
            return json.loads(bloco)
        except Exception:
            return json_repair.loads(bloco)
    return json_repair.loads(texto)

def _analisar(ag_analista: Agent, ctx: Dict[str, str], mensagens: List[Dict[str, Any]], cfg: Dict[str, Any], tentativas: int = 3) -> Dict[str, Any]:
    ultimo_raw = ""
    idioma = cfg.get("idioma", "português do Brasil")
    for _ in range(tentativas):
        task = Task(
            description=f"""Analise a conversa comercial abaixo, em que a empresa tentou oferecer o serviço descrito.

SERVIÇO:
{ctx['servico']}

PERFIL DO CLIENTE:
{ctx['cliente']}

NATUREZA DO CONTATO:
{ctx['contato']}

CONVERSA:
{_formatar(mensagens)}

Classifique o resultado e extraia insights, em {idioma}.
Considere "sucesso" apenas se o cliente aceitou ou se comprometeu claramente com um próximo passo concreto de contratação.
Responda SOMENTE com um objeto JSON válido, sem texto antes ou depois, neste formato:
{SCHEMA_JSON}""",
            expected_output="Um objeto JSON válido conforme o formato indicado.",
            agent=ag_analista,
        )
        crew = Crew(agents=[ag_analista], tasks=[task], process=Process.sequential, verbose=False)
        ultimo_raw = str(crew.kickoff().raw)
        try:
            dados = _extrair_json(ultimo_raw)
            return AnaliseNegociacao.model_validate(dados).model_dump()
        except (ValueError, ValidationError, json.JSONDecodeError):
            continue
    return {
        "resultado": "indefinido",
        "confianca": 0,
        "justificativa": "Falha ao estruturar a análise.",
        "raw": ultimo_raw,
    }

async def _analisar_async(ag_analista: Agent, ctx: Dict[str, str], mensagens: List[Dict[str, Any]], cfg: Dict[str, Any], tentativas: int = 3) -> Dict[str, Any]:
    ultimo_raw = ""
    idioma = cfg.get("idioma", "português do Brasil")
    for _ in range(tentativas):
        task = Task(
            description=f"""Analise a conversa comercial abaixo, em que a empresa tentou oferecer o serviço descrito.

SERVIÇO:
{ctx['servico']}

PERFIL DO CLIENTE:
{ctx['cliente']}

NATUREZA DO CONTATO:
{ctx['contato']}

CONVERSA:
{_formatar(mensagens)}

Classifique o resultado e extraia insights, em {idioma}.
Considere "sucesso" apenas se o cliente aceitou ou se comprometeu claramente com um próximo passo concreto de contratação.
Responda SOMENTE com um objeto JSON válido, sem texto antes ou depois, neste formato:
{SCHEMA_JSON}""",
            expected_output="Um objeto JSON válido conforme o formato indicado.",
            agent=ag_analista,
        )
        crew = Crew(agents=[ag_analista], tasks=[task], process=Process.sequential, verbose=False)
        saida = await crew.kickoff_async()
        ultimo_raw = str(saida.raw)
        try:
            dados = _extrair_json(ultimo_raw)
            return AnaliseNegociacao.model_validate(dados).model_dump()
        except (ValueError, ValidationError, json.JSONDecodeError):
            continue
    return {
        "resultado": "indefinido",
        "confianca": 0,
        "justificativa": "Falha ao estruturar a análise.",
        "raw": ultimo_raw,
    }

# ---------- Resolução de Diretórios ----------
def resolver_diretorios(cfg: Dict[str, Any]) -> tuple[Path, Path, Path]:
    exec_dir = Path(cfg.get("exec_dir") or EXEC_DIR_PADRAO)
    base_dir = Path(cfg.get("base_dir") or (exec_dir / "kb"))
    saida_dir = Path(cfg.get("saida_dir") or (exec_dir / "resultados"))

    exec_dir.mkdir(parents=True, exist_ok=True)
    saida_dir.mkdir(parents=True, exist_ok=True)
    garantir_base(base_dir)

    return exec_dir, base_dir, saida_dir

# ---------- Simulação síncrona ----------
def simular(cfg: Dict[str, Any]) -> Dict[str, Any]:
    _, base_dir, saida_dir = resolver_diretorios(cfg)

    ctx = {cat: carregar_item(base_dir, cat, cfg[cat])
           for cat in ["empresa", "cliente", "servico", "contato"]}
    iniciador = cfg.get("iniciador") or detectar_iniciador(ctx["contato"])
    ag_empresa, ag_cliente, ag_analista = criar_agentes(ctx, cfg)
    agentes = {"empresa": ag_empresa, "cliente": ag_cliente}
    ordem = ["empresa", "cliente"] if iniciador == "empresa" else ["cliente", "empresa"]

    mensagens, encerrou = [], False
    trocas_total = cfg.get("trocas", 6)
    for troca in range(1, trocas_total + 1):
        for quem in ordem:
            ultima = (troca == trocas_total)
            bruto = _falar(
                agentes[quem],
                quem,
                _formatar(mensagens),
                primeira_fala=(not mensagens),
                cfg=cfg,
                ultima_rodada=ultima,
            )
            fim = MARCADOR_FIM in bruto
            texto = _limpar(bruto.replace(MARCADOR_FIM, ""))
            mensagens.append({"troca": troca, "autor": quem, "texto": texto})
            if cfg.get("verbose", True):
                print(f"[{troca}] {quem.upper()}: {texto}\n")
            if fim and cfg.get("encerramento_antecipado", True):
                encerrou = True
                break
        if encerrou:
            break

    analise = _analisar(ag_analista, ctx, mensagens, cfg)

    resultado = {
        "configuracao": {
            k: cfg[k]
            for k in ["empresa", "cliente", "servico", "contato", "trocas", "modelo", "exec_dir", "base_dir", "saida_dir"]
            if k in cfg
        },
        "iniciador": iniciador,
        "encerrou_antecipadamente": encerrou,
        "trocas_realizadas": max(m["troca"] for m in mensagens) if mensagens else 0,
        "conversa": mensagens,
        "analise": analise,
    }

    nome = f"sim_{datetime.now():%Y%m%d_%H%M%S}.json"
    caminho_arq = saida_dir / nome
    caminho_arq.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    resultado["arquivo"] = str(caminho_arq)

    return resultado

# ---------- Simulação assíncrona ----------
async def simular_async(cfg: Dict[str, Any]) -> Dict[str, Any]:
    _, base_dir, saida_dir = resolver_diretorios(cfg)

    ctx = {cat: carregar_item(base_dir, cat, cfg[cat])
           for cat in ["empresa", "cliente", "servico", "contato"]}
    iniciador = cfg.get("iniciador") or detectar_iniciador(ctx["contato"])
    ag_empresa, ag_cliente, ag_analista = criar_agentes(ctx, cfg)
    agentes = {"empresa": ag_empresa, "cliente": ag_cliente}
    ordem = ["empresa", "cliente"] if iniciador == "empresa" else ["cliente", "empresa"]

    mensagens, encerrou = [], False
    trocas_total = cfg.get("trocas", 6)
    for troca in range(1, trocas_total + 1):
        for quem in ordem:
            ultima = (troca == trocas_total)
            bruto = await _falar_async(
                agentes[quem],
                quem,
                _formatar(mensagens),
                primeira_fala=(not mensagens),
                cfg=cfg,
                ultima_rodada=ultima,
            )
            fim = MARCADOR_FIM in bruto
            texto = _limpar(bruto.replace(MARCADOR_FIM, ""))
            mensagens.append({"troca": troca, "autor": quem, "texto": texto})
            if cfg.get("verbose", True):
                print(f"[{troca}] {quem.upper()}: {texto}\n")
            if fim and cfg.get("encerramento_antecipado", True):
                encerrou = True
                break
        if encerrou:
            break

    analise = await _analisar_async(ag_analista, ctx, mensagens, cfg)

    resultado = {
        "configuracao": {
            k: cfg[k]
            for k in ["empresa", "cliente", "servico", "contato", "trocas", "modelo", "exec_dir", "base_dir", "saida_dir"]
            if k in cfg
        },
        "iniciador": iniciador,
        "encerrou_antecipadamente": encerrou,
        "trocas_realizadas": max(m["troca"] for m in mensagens) if mensagens else 0,
        "conversa": mensagens,
        "analise": analise,
    }

    nome = f"sim_{datetime.now():%Y%m%d_%H%M%S}.json"
    caminho_arq = saida_dir / nome
    caminho_arq.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    resultado["arquivo"] = str(caminho_arq)

    return resultado

# ---------- Exibição ----------
def mostrar(resultado: Dict[str, Any]) -> None:
    a = resultado.get("analise", {})
    res_str = str(a.get("resultado", "")).lower()
    icone = {"sucesso": "✅", "insucesso": "❌"}.get(res_str, "❔")
    print("=" * 70)
    print(f"{icone} RESULTADO: {res_str.upper()} (confiança: {a.get('confianca','?')}%)")
    print(
        f"Trocas realizadas: {resultado.get('trocas_realizadas')} | "
        f"Encerrou antes: {resultado.get('encerrou_antecipadamente')}"
    )
    print("-" * 70)
    print("Justificativa:", a.get("justificativa", a.get("raw", "")))
    print("Momento decisivo:", a.get("momento_decisivo", "-"))
    for titulo, chave in [
        ("Objeções do cliente", "objecoes_cliente"),
        ("Estratégias que funcionaram", "estrategias_que_funcionaram"),
        ("Erros da empresa", "erros_da_empresa"),
        ("Recomendações", "recomendacoes"),
    ]:
        print(f"\n{titulo}:")
        for item in a.get(chave, []):
            print(f"  - {item}")
    if "arquivo" in resultado:
        print(f"\nArquivo salvo em: {resultado['arquivo']}")
    print("=" * 70)

# Configuração padrão da simulação
CONFIG = {
    # Diretórios de execução
    "exec_dir": str(EXEC_DIR_PADRAO),
    "base_dir": str(BASE_KB_PADRAO),
    "saida_dir": str(SAIDA_PADRAO),

    # Perfis selecionados da base de conhecimento
    "empresa": "empresa_alfa",
    "cliente": "cliente_receptivo_mariana",
    "servico": "plano_fibra_negocios",
    "contato": "receptivo_problema",
    "iniciador": None,
    "trocas": 5,
    "encerramento_antecipado": True,

    # LLM (Google Gemini)
    "provedor": "gemini",
    "modelo": "gemini-3.8-flash",
    "temperatura_empresa": 0.6,
    "temperatura_cliente": 0.8,
    "max_tokens_fala": 250,
    "max_tokens_analise": 1500,
    "idioma": "português do Brasil",

    "verbose": True,
}

if __name__ == "__main__":
    exec_dir, base_dir, saida_dir = resolver_diretorios(CONFIG)
    print(f"Iniciando simulação com CrewAI e Google Gemini ({CONFIG['modelo']})...\n")
    print(f"Diretórios:")
    print(f"  - Execução: {exec_dir}")
    print(f"  - Base de conhecimento (KB): {base_dir}")
    print(f"  - Resultados: {saida_dir}")
    print(f"Perfis:")
    print(f"  - Empresa: {CONFIG['empresa']}")
    print(f"  - Cliente: {CONFIG['cliente']}")
    print(f"  - Serviço: {CONFIG['servico']}")
    print(f"  - Contato: {CONFIG['contato']}")
    print("-" * 70 + "\n")

    resultado = simular(CONFIG)
    mostrar(resultado)
