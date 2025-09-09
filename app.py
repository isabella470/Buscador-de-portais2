import streamlit as st
import pandas as pd
import io
from urllib.parse import urlparse
from duckduckgo_search import ddg

# --- Configuração da Página do Streamlit ---
st.set_page_config(page_title="Buscador de Portais", page_icon="🔎", layout="wide")

st.title("🔎 Buscador Automatizado de Portais")
st.markdown("A ferramenta buscará no DuckDuckGo para encontrar os sites.")

# --- Interface do Usuário ---
if 'resultados_df' not in st.session_state:
    st.session_state.resultados_df = None

input_text = st.text_area(
    "Cole a lista de portais aqui (um por linha):", 
    height=250, 
    placeholder="Rádio Santana FM\nPortal Guaraciaba Notícias\nIpu Notícias..."
)

def realizar_busca(query, num_resultados=5):
    resultados = ddg(query, max_results=num_resultados)
    urls_encontradas = []
    if resultados:
        for r in resultados:
            urls_encontradas.append(r["href"])
    return urls_encontradas

if st.button("🚀 Iniciar Busca"):
    if not input_text.strip():
        st.warning("Por favor, insira pelo menos um nome na lista.")
    else:
        lista_de_buscas = [line.strip() for line in input_text.split('\n') if line.strip()]
        df_final = pd.DataFrame()

        with st.spinner("Aguarde... a busca está em andamento..."):
            for i, nome_busca in enumerate(lista_de_buscas):
                st.info(f"Buscando por: '{nome_busca}' ({i+1}/{len(lista_de_buscas)})")
                resultados_gerais = realizar_busca(f'"{nome_busca}"')
                if resultados_gerais:
                    for url in resultados_gerais:
                        dominio = urlparse(url).netloc.replace("www.", "")
                        nova_linha = pd.DataFrame([{
                            "Fonte Pesquisada": nome_busca, 
                            "Site (Domínio)": dominio, 
                            "URL": url
                        }])
                        df_final = pd.concat([df_final, nova_linha], ignore_index=True)
                else:
                    nova_linha = pd.DataFrame([{
                        "Fonte Pesquisada": nome_busca, 
                        "Site (Domínio)": "N/A", 
                        "URL": "Nenhum resultado encontrado"
                    }])
                    df_final = pd.concat([df_final, nova_linha], ignore_index=True)

        st.success("✅ Busca finalizada com sucesso!")
        st.session_state.resultados_df = df_final

# --- Seção de Resultados ---
if st.session_state.resultados_df is not None:
    st.dataframe(st.session_state.resultados_df)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        st.session_state.resultados_df.to_excel(writer, index=False, sheet_name='Resultados')
    st.download_button(
        label="📥 Baixar resultados em Excel",
        data=output.getvalue(),
        file_name="resultados_buscas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


