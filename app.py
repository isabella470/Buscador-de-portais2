# Conteúdo ATUALIZADO E MAIS LEVE para o seu arquivo app.py

import streamlit as st
import time
from googlesearch import search
import io
import csv # Biblioteca nativa do Python para ler arquivos de texto com vírgulas

# --- Nova Função para gerar um arquivo CSV para download ---
def to_csv_string(lista_de_dados):
    output = io.StringIO()
    # Pega os cabeçalhos do primeiro item da lista
    if not lista_de_dados:
        return ""
    headers = lista_de_dados[0].keys()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(lista_de_dados)
    return output.getvalue()

# --- Interface da Aplicação ---
st.set_page_config(page_title="Buscador de Sites", page_icon="🌐")

st.title("🌐 Buscador de Sites de Portais (v4 - TXT)") # Mudei para v4
st.markdown("""
Esta ferramenta automatiza a busca por sites de veículos de comunicação a partir de um arquivo de texto (.txt).
**Formato do .txt:** A primeira linha deve ser `nome,regiao`. As linhas seguintes devem ter o nome do veículo, uma vírgula, e a região.
""")

uploaded_file = st.file_uploader(
    "Faça o upload do seu arquivo .txt aqui",
    type=['txt'] # Agora aceita .txt
)

if uploaded_file is not None:
    try:
        # --- Nova lógica para ler o arquivo TXT ---
        # O arquivo vem como bytes, então decodificamos para texto
        string_data = uploaded_file.getvalue().decode('utf-8')
        # Usamos a biblioteca CSV para ler o texto de forma estruturada
        reader = csv.DictReader(io.StringIO(string_data))
        lista_de_veiculos = list(reader)
        
        st.success(f"Arquivo '{uploaded_file.name}' carregado com sucesso!")
        st.write(f"Encontrados {len(lista_de_veiculos)} veículos para pesquisar.")

        if st.button("🚀 Iniciar Busca de Sites", type="primary"):
            resultados_finais = []
            total_rows = len(lista_de_veiculos)
            progress_bar = st.progress(0, text="Iniciando...")
            status_text = st.empty()

            for index, veiculo in enumerate(lista_de_veiculos):
                try:
                    nome = veiculo.get('nome', '')
                    regiao = veiculo.get('regiao', '')
                    query = f"{nome} {regiao} portal de notícias site oficial"
                    
                    progress_text = f"Buscando por: {nome}... ({index + 1}/{total_rows})"
                    status_text.text(progress_text)
                    progress_bar.progress((index + 1) / total_rows, text=progress_text)

                    search_result = search(query, num_results=1, lang='pt-br', sleep_interval=5)
                    
                    if search_result:
                        veiculo['Site_Encontrado'] = search_result[0]
                    else:
                        veiculo['Site_Encontrado'] = "Não encontrado"
                
                except Exception as e:
                    error_message = f"Erro na busca por '{nome}'. Motivo: {e}"
                    st.error(error_message)
                    veiculo['Site_Encontrado'] = "Falha na busca"
                
                resultados_finais.append(veiculo)

            status_text.success("✅ Busca concluída!")
            st.session_state.final_data = resultados_finais

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
        st.warning("Verifique se o arquivo .txt está no formato correto (separado por vírgulas).")

if 'final_data' in st.session_state:
    st.markdown("---")
    st.subheader("Resultados da Busca")
    final_data = st.session_state.final_data
    st.dataframe(final_data) # st.dataframe funciona bem com lista de dicionários!
    
    csv_string = to_csv_string(final_data)
    
    st.download_button(
        label="📥 Baixar Resultados em CSV",
        data=csv_string,
        file_name="sites_encontrados.csv",
        mime="text/csv"
    )

