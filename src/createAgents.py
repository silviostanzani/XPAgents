import os
import re
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from crewai import Agent, LLM

def carregar_gemini_api_key() -> Optional[str]:
    """Carrega a chave de API do Gemini da variável de ambiente ou do ~/.bashrc."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()

    bashrc = Path.home() / ".bashrc"
    if bashrc.exists():
        for line in bashrc.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("export GEMINI_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    os.environ["GEMINI_API_KEY"] = val
                    return val
    return None

def criar_llm(cfg: Dict[str, Any], temperatura: float, max_tokens: int) -> LLM:
    """Instancia o LLM configurado (Google Gemini, Ollama ou outro)."""
    modelo = cfg.get("modelo", "gemini-3.8-flash")
    provedor = cfg.get("provedor", "gemini")

    if provedor == "gemini" or "gemini" in modelo.lower():
        api_key = cfg.get("api_key") or carregar_gemini_api_key()
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY não encontrada nas variáveis de ambiente nem em ~/.bashrc"
            )
        os.environ["GEMINI_API_KEY"] = api_key
        model_name = modelo if modelo.startswith("gemini/") else f"gemini/{modelo}"
        return LLM(
            model=model_name,
            temperature=temperatura,
            max_tokens=max_tokens,
            api_key=api_key,
        )
    elif provedor == "ollama" or "ollama" in modelo.lower():
        model_name = modelo if modelo.startswith("ollama/") else f"ollama/{modelo}"
        return LLM(
            model=model_name,
            base_url=cfg.get("ollama_url", "http://127.0.0.1:11434"),
            temperature=temperatura,
            max_tokens=max_tokens,
        )
    else:
        return LLM(
            model=modelo,
            temperature=temperatura,
            max_tokens=max_tokens,
        )

def criar_agentes(ctx: Dict[str, str], cfg: Dict[str, Any]) -> Tuple[Agent, Agent, Agent]:
    """Cria os agentes da empresa, do cliente e do analista."""
    idioma = cfg.get("idioma", "português do Brasil")
    llm_empresa = criar_llm(cfg, cfg.get("temperatura_empresa", 0.6), cfg.get("max_tokens_fala", 250))
    llm_cliente = criar_llm(cfg, cfg.get("temperatura_cliente", 0.8), cfg.get("max_tokens_fala", 250))
    llm_analista = criar_llm(cfg, 0.1, cfg.get("max_tokens_analise", 1200))

    empresa = Agent(
        role="Representante comercial da empresa",
        goal="Conduzir o contato de forma natural e, quando fizer sentido, apresentar e fechar o novo serviço respeitando as políticas da empresa.",
        backstory=f"""Você representa a empresa descrita abaixo, em conversa por mensagens, em {idioma}.

PERFIL DA EMPRESA:
{ctx['empresa']}

SERVIÇO A SER OFERECIDO:
{ctx['servico']}

NATUREZA DO CONTATO:
{ctx['contato']}

Regras: seja realista e humano, mensagens curtas (1 a 4 frases), não invente condições fora das políticas
da empresa, não revele que é uma IA, adapte a abordagem ao que o cliente demonstra.""",
        llm=llm_empresa,
        allow_delegation=False,
        verbose=False,
    )

    cliente = Agent(
        role="Cliente",
        goal="Reagir de forma realista à conversa, de acordo com seu perfil, decidindo se o serviço vale a pena para você.",
        backstory=f"""Você é o cliente descrito abaixo, em conversa por mensagens, em {idioma}.

PERFIL DO CLIENTE:
{ctx['cliente']}

NATUREZA DO CONTATO:
{ctx['contato']}

Regras: aja como uma pessoa real, mensagens curtas e naturais, não facilite demais: só aceite se os
argumentos realmente atenderem às suas motivações e barreiras. Pode recusar, pedir tempo, comparar com
concorrentes ou encerrar. Você NÃO conhece detalhes internos da empresa além do que ela disser.
Não revele que é uma IA.""",
        llm=llm_cliente,
        allow_delegation=False,
        verbose=False,
    )

    analista = Agent(
        role="Analista de negociações comerciais",
        goal="Avaliar objetivamente o desfecho da conversa e extrair insights acionáveis.",
        backstory="Especialista em vendas consultivas e análise de conversas comerciais. Imparcial e baseado em evidências do texto.",
        llm=llm_analista,
        allow_delegation=False,
        verbose=False,
    )

    return empresa, cliente, analista
