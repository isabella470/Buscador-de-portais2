import streamlit as st
import pandas as pd
import io
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time

# --- Configuração da Página do Streamlit ---
st.set_page_config(page_title="Buscador de Portais", page_icon="🔎", layout="wide")

st.title("🔎 Buscador Automatizado de Portais (Gratuito)")
st.markdown("A ferramenta buscará no DuckDuckGo (versão HTML) para encontrar os sites oficiais dos portais.")

# --- Função de busca via requests + BeautifulSoup ---
def buscar_site_portal(query, max_results=3):
    resultados = []
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}  # simula navegador
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = soup.select("a.result__a")  # seletor de links da versão HTML
        for link in links[:max_results]:
            href = link.get("href")
            if href and href.startswith("http"):
                resultados.append(href)
        time.sleep(2)  # delay para reduzir risco de bloqueio
    except Exception as e:
        st.warning(f"Erro na busca por '{query}': {e}")
    return resultados

# --- Estado inicial ---
if 'resultados_df' not in st.session_state:
    st.session_state.resultados_df = None

# --- Área de input ---
input_text = st.text_area(
    "Cole a lista de portais aqui (um por linha):", 
    height=250, 
    placeholder="Rádio Santana FM\nPortal Guaraciaba Notícias\nIpu Notícias..."
)

# --- Botão de busca ---
if st.button("🚀 Iniciar Busca"):
    if not input_text.strip():
        st.warning("Por favor, insira pelo menos um nome na lista.")
    else:
        lista_de_buscas = [line.strip() for line in input_text.split('\n') if line.strip()]
        df_final = pd.DataFrame()

        with st.spinner("Aguarde... a busca está em andamento..."):
            for i, nome_busca in enumerate(lista_de_buscas):
                st.info(f"Buscando por: '{nome_busca}' ({i+1}/{len(lista_de_buscas)})")
                resultados_gerais = buscar_site_portal(f'"{nome_busca}"')
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


