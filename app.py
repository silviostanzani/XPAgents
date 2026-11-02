import streamlit as st
import json
import os
import glob
import pandas as pd

st.set_page_config(page_title="XPAgents - Dashboard & KB", layout="wide")

RESULTS_DIR = "/home/silvio/XPAgents/resultados"
KB_DIR = "/home/silvio/XPAgents/kb"

@st.cache_data
def load_data():
    json_files = glob.glob(os.path.join(RESULTS_DIR, "*.json"))
    data = []
    for f in json_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = json.load(file)
                content['filename'] = os.path.basename(f)
                data.append(content)
        except Exception as e:
            st.error(f"Erro ao ler {f}: {e}")
    return sorted(data, key=lambda x: x['filename'], reverse=True)

st.sidebar.title("Navegação")
menu = st.sidebar.radio("Ir para:", ["📊 Dashboard de Simulações", "✏️ Editor da Base de Conhecimento", "🚀 Executar Simulação"])

if menu == "📊 Dashboard de Simulações":
    col_title, col_btn = st.columns([8, 1])
    with col_title:
        st.title("📊 Resultados das Simulações")
    with col_btn:
        st.write("")
        if st.button("🔄 Atualizar"):
            load_data.clear()
            st.rerun()

    
    data = load_data()
    
    if not data:
        st.warning(f"Nenhum arquivo JSON encontrado na pasta {RESULTS_DIR}.")
    else:
        st.sidebar.markdown("---")
        st.sidebar.header("📁 Selecione a Simulação")
        filenames = [d['filename'] for d in data]
        selected_file = st.sidebar.selectbox("Arquivo de resultado", filenames)
        
        selected_data = next((d for d in data if d['filename'] == selected_file), None)
        
        if selected_data:
            st.sidebar.markdown("---")
            st.sidebar.subheader("Resumo da Execução")
            cfg = selected_data.get('configuracao', {})
            st.sidebar.write(f"**Empresa:** {cfg.get('empresa', '-')}")
            st.sidebar.write(f"**Cliente:** {cfg.get('cliente', '-')}")
            st.sidebar.write(f"**Serviço:** {cfg.get('servico', '-')}")
            st.sidebar.write(f"**Modelo:** {cfg.get('modelo', '-')}")
            st.sidebar.write(f"**Trocas Realizadas:** {selected_data.get('trocas_realizadas', '-')}/{cfg.get('trocas', '-')}")

            tab1, tab2, tab3 = st.tabs(["📈 Análise de Resultado", "💬 Histórico da Conversa", "📚 Base de Conhecimento Usada"])

            with tab1:
                analise = selected_data.get('analise', {})
                if analise:
                    resultado = analise.get('resultado', 'desconhecido')
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Resultado", resultado.upper())
                    col2.metric("Confiança", f"{analise.get('confianca', 0)}%")
                    col3.metric("Encerrou Antecipadamente?", "Sim" if selected_data.get("encerrou_antecipadamente") else "Não")

                    st.markdown(f"### Justificativa\n{analise.get('justificativa', '-')}")
                    st.markdown(f"### Momento Decisivo\n{analise.get('momento_decisivo', '-')}")
                    
                    st.markdown("---")
                    col_list1, col_list2 = st.columns(2)
                    
                    with col_list1:
                        st.subheader("🎯 Estratégias que Funcionaram")
                        for est in analise.get('estrategias_que_funcionaram', []):
                            st.markdown(f"- ✅ {est}")
                            
                        st.subheader("💡 Recomendações")
                        for rec in analise.get('recomendacoes', []):
                            st.markdown(f"- 📌 {rec}")
                            
                    with col_list2:
                        st.subheader("🛡️ Objeções do Cliente")
                        for obj in analise.get('objecoes_cliente', []):
                            st.markdown(f"- 🛑 {obj}")
                            
                        st.subheader("⚠️ Erros da Empresa")
                        for err in analise.get('erros_da_empresa', []):
                            st.markdown(f"- ❌ {err}")
                else:
                    st.info("Nenhuma análise final encontrada para esta simulação.")

            with tab2:
                st.subheader("Registro da Conversa")
                conversa = selected_data.get('conversa', [])
                for msg in conversa:
                    autor = msg.get('autor', 'desconhecido')
                    texto = msg.get('texto', '')
                    troca = msg.get('troca', '-')
                    
                    if autor == 'empresa':
                        with st.chat_message("assistant", avatar="🏢"):
                            st.caption(f"Troca {troca} - Empresa")
                            st.write(texto)
                    elif autor == 'cliente':
                        with st.chat_message("user", avatar="👤"):
                            st.caption(f"Troca {troca} - Cliente")
                            st.write(texto)
                    else:
                        with st.chat_message("user"):
                            st.caption(f"Troca {troca} - {autor}")
                            st.write(texto)
                            
            with tab3:
                st.subheader("Base de Conhecimento Utilizada")
                kb_mapping = {
                    "Empresa": ("empresa", cfg.get('empresa')),
                    "Cliente": ("cliente", cfg.get('cliente')),
                    "Serviço": ("servico", cfg.get('servico')),
                    "Contato": ("contato", cfg.get('contato')),
                }
                
                for label, (pasta, nome_arquivo) in kb_mapping.items():
                    if not nome_arquivo:
                        st.info(f"Nenhum arquivo de {label} especificado na configuração.")
                        continue
                        
                    caminho_base = os.path.join(KB_DIR, pasta, nome_arquivo)
                    caminho_md = f"{caminho_base}.md"
                    caminho_txt = f"{caminho_base}.txt"
                    
                    arquivo_encontrado = None
                    if os.path.exists(caminho_md):
                        arquivo_encontrado = caminho_md
                    elif os.path.exists(caminho_txt):
                        arquivo_encontrado = caminho_txt
                        
                    with st.expander(f"📄 {label}: {nome_arquivo}", expanded=False):
                        if arquivo_encontrado:
                            try:
                                with open(arquivo_encontrado, 'r', encoding='utf-8') as f:
                                    conteudo_kb = f.read()
                                st.markdown(conteudo_kb)
                            except Exception as e:
                                st.error(f"Erro ao ler o arquivo {arquivo_encontrado}: {e}")
                        else:
                            st.warning(f"Arquivo não encontrado em {KB_DIR}/{pasta}/{nome_arquivo}.[md|txt]")

elif menu == "✏️ Editor da Base de Conhecimento":
    st.title("✏️ Editor da Base de Conhecimento (KB)")
    
    kb_categories = ["cliente", "contato", "empresa", "servico"]
    
    col_nav, col_editor = st.columns([1, 2.5])
    
    with col_nav:
        st.subheader("1. Selecione a Categoria")
        selected_category = st.selectbox("📁 Pasta", kb_categories)
        
        category_path = os.path.join(KB_DIR, selected_category)
        if not os.path.exists(category_path):
            os.makedirs(category_path, exist_ok=True)
            
        files_in_category = glob.glob(os.path.join(category_path, "*.md")) + glob.glob(os.path.join(category_path, "*.txt"))
        file_names = [os.path.basename(f) for f in files_in_category]
        
        st.subheader("2. Selecione o Arquivo")
        selected_kb_file = st.selectbox("📄 Arquivo", ["-- Criar Novo Arquivo --"] + sorted(file_names))
        
        if selected_kb_file == "-- Criar Novo Arquivo --":
            new_file_name = st.text_input("Nome do novo arquivo (sem extensão)")
            new_file_ext = st.selectbox("Extensão", [".md", ".txt"])
            
            if new_file_name:
                safe_name = new_file_name.strip().replace(" ", "_")
                current_file_path = os.path.join(category_path, safe_name + new_file_ext)
                content_to_edit = ""
            else:
                current_file_path = None
                content_to_edit = ""
        else:
            current_file_path = os.path.join(category_path, selected_kb_file)
            try:
                with open(current_file_path, 'r', encoding='utf-8') as f:
                    content_to_edit = f.read()
            except Exception as e:
                st.error(f"Erro ao ler arquivo: {e}")
                content_to_edit = ""
                current_file_path = None
                
    with col_editor:
        if current_file_path:
            st.subheader(f"Editando: `{os.path.basename(current_file_path)}`")
            new_content = st.text_area("Conteúdo do Arquivo", value=content_to_edit, height=600)
            
            if st.button("💾 Salvar Alterações", type="primary"):
                try:
                    with open(current_file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    st.success(f"Arquivo `{os.path.basename(current_file_path)}` salvo com sucesso na pasta `{selected_category}`!")
                except Exception as e:
                    st.error(f"Erro ao salvar arquivo: {e}")
        else:
            st.info("👈 Selecione um arquivo existente à esquerda ou digite um nome para criar um novo arquivo.")

elif menu == "🚀 Executar Simulação":
    import subprocess
    st.title("🚀 Executar Nova Simulação")
    st.write("Configure os parâmetros abaixo e inicie uma nova simulação.")
    
    col1, col2 = st.columns(2)
    
    def get_options_for(category):
        path = os.path.join(KB_DIR, category)
        if not os.path.exists(path):
            return []
        files = glob.glob(os.path.join(path, "*.md")) + glob.glob(os.path.join(path, "*.txt"))
        names = [os.path.splitext(os.path.basename(f))[0] for f in files]
        return sorted(list(set(names)))
        
    with col1:
        st.subheader("📚 Perfis Base (KB)")
        empresa = st.selectbox("Empresa", get_options_for("empresa"))
        cliente = st.selectbox("Cliente", get_options_for("cliente"))
        servico = st.selectbox("Serviço", get_options_for("servico"))
        contato = st.selectbox("Contato", get_options_for("contato"))
        
    with col2:
        st.subheader("⚙️ Parâmetros Técnicos")
        iniciador = st.selectbox("Quem Inicia?", ["cliente", "empresa", ""])
        modelo = st.text_input("Modelo LLM", value="gemini-3.8-flash")
        trocas = st.number_input("Número de Trocas", min_value=1, max_value=20, value=6)
        encerra = st.checkbox("Permitir Encerramento Antecipado", value=True)
        temp_emp = st.slider("Temperatura Empresa", 0.0, 1.0, 0.6)
        temp_cli = st.slider("Temperatura Cliente", 0.0, 1.0, 0.8)
        
    if st.button("▶️ Iniciar Simulação", type="primary"):
        config = {
            "empresa": empresa,
            "cliente": cliente,
            "servico": servico,
            "contato": contato,
            "iniciador": iniciador if iniciador else None,
            "modelo": modelo,
            "trocas": trocas,
            "encerramento_antecipado": encerra,
            "temperatura_empresa": temp_emp,
            "temperatura_cliente": temp_cli
        }
        
        config_path = "/tmp/sim_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f)
            
        st.info("Simulação iniciada! Aguarde a conclusão... O processo pode levar de alguns segundos a minutos dependendo do LLM.")
        
        # Executing the simulation script
        script_path = "/home/silvio/git/XPAgents/src/Simulation.py"
        try:
            # We assume python3 or the current environment python is appropriate.
            # Using st.spinner to hold the UI
            with st.spinner("Rodando agentes..."):
                result = subprocess.run(
                    ["python3", script_path, "--config", config_path],
                    capture_output=True,
                    text=True
                )
            
            if result.returncode == 0:
                st.success("✅ Simulação concluída com sucesso!")
                with st.expander("Ver Log da Execução"):
                    st.text(result.stdout)
                # Clear cache so next time Dashboard is loaded it shows the new simulation
                load_data.clear()
            else:
                st.error("❌ Erro na simulação.")
                with st.expander("Ver Erro"):
                    st.text(result.stderr)
                    st.text(result.stdout)
                    
        except Exception as e:
            st.error(f"Erro ao executar processo: {e}")
