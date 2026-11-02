# XPAgents

Simulador de experiências e negociações comerciais entre clientes e representantes de empresas utilizando **CrewAI** e LLMs (como **Google Gemini 3.8 Flash**).

## Diretório de Execução Padrão

Por padrão, a base de conhecimento (`kb/`) e os arquivos de saída das simulações (`resultados/`) ficam centralizados em:

```
/home/silvio/XPAgents/
├── kb/
│   ├── cliente/
│   ├── contato/
│   ├── empresa/
│   └── servico/
└── resultados/
    └── sim_YYYYMMDD_HHMMSS.json
```

> **Nota:** É possível customizar o diretório de execução definindo a chave `"exec_dir"` no dicionário `CONFIG` ou exportando a variável de ambiente `XPAGENTS_WORK_DIR`. Se o diretório `kb/` estiver ausente, o simulador inicializa automaticamente os perfis padrão.

---

## Como Funciona o Simulador

O simulador modela conversas comerciais realistas orientadas por perfis e regras detalhadas, divididas em quatro etapas principais:

1. **Base de Conhecimento (`kb/`)**:
   - `empresa/`: Perfil institucional, tom de voz, regras de negócio e políticas de desconto.
   - `cliente/`: Persona do cliente (dores, perfil financeiro, ceticismo, critérios de aceitação e motivos de recusa).
   - `servico/`: Especificações técnicas da oferta, valores, diferenciais e limitações.
   - `contato/`: Contexto do contato (ativo de vendas, receptivo de dúvida, receptivo de problema) e quem inicia o diálogo (`iniciador: empresa` ou `iniciador: cliente`).

2. **Agentes CrewAI (`src/createAgents.py`)**:
   - **Empresa**: Atua como o consultor/vendedor, respeitando as regras e políticas comerciais.
   - **Cliente**: Reage de forma realista às mensagens, aceitando apenas quando suas necessidades e critérios são atendidos.
   - **Analista**: Especialista neutro que audita a conversa e gera métricas estruturadas.

3. **Loop de Conversação Turno a Turno (`src/Simulation.py`)**:
   - Executa a troca de mensagens de forma sequencial.
   - Suporta detecção de desfecho antecipado via marcador `[FIM]`.

4. **Análise Estruturada e Validação**:
   - O agente analista avalia o resultado (`sucesso`, `insucesso` ou `indefinido`), nível de confiança (0 a 100%), momento decisivo, objeções levantadas, estratégias eficientes, erros e recomendações práticas.
   - O resultado é validado via Pydantic e gravado em formato JSON na pasta `resultados/`.

---

## Requisitos e Configuração

- Python 3.10+ (ou ambiente Conda como `gemini2`)
- Chave de API Google Gemini definida na variável de ambiente `GEMINI_API_KEY` ou no arquivo `~/.bashrc`.

### Dependências

```bash
pip install -q crewai pydantic requests json-repair
```

---

## Execução

Para rodar a simulação com o Google Gemini 3.8 Flash:

```bash
/home/silvio/miniconda3/envs/gemini2/bin/python src/Simulation.py
```

Ou ativando o ambiente conda:

```bash
conda activate gemini2
python src/Simulation.py
```
