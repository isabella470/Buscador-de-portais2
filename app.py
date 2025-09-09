import streamlit as st
import pandas as pd
import time
import io
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.opera.service import Service as OperaService
from selenium.webdriver.opera.options import Options
from webdriver_manager.opera import OperaDriverManager

# --- Configuração da Página do Streamlit ---
st.set_page_config(page_title="Buscador com Opera", page_icon="🅾️", layout="wide")

st.title("🅾️ Buscador Automatizado com Opera")
st.markdown("A ferramenta usará o navegador Opera instalado no seu computador para buscar no DuckDuckGo.")

# --- Cache para o WebDriver ---
@st.cache_resource
def get_driver():
    """
    Inicializa o driver do Selenium para o Opera,
    gerenciando o operadriver automaticamente.
    """
    st.info("Inicializando o navegador Opera...")
    # Opções específicas do Opera (são baseadas nas do Chromium)
    opera_options = Options()
    opera_options.add_argument("--headless") # Roda o navegador em segundo plano
    opera_options.add_argument("--no-sandbox")
    opera_options.add_argument("--disable-gpu")
    
    # Instala e gerencia o operadriver automaticamente
    service = OperaService(OperaDriverManager().install())
    driver = webdriver.Opera(service=service, options=opera_options)
    st.info("Navegador pronto.")
    return driver

def realizar_busca(driver, query, num_resultados=5):
    """
    Função para buscar no DuckDuckGo (alternativa ao Google)
    e extrair links usando um seletor estável.
    """
    urls_encontradas = []
    try:
        query_formatada = query.replace(" ", "+")
        # Usando o motor de busca DuckDuckGo (versão HTML, mais leve)
        url_busca = f"https://html.duckduckgo.com/html/?q={query_formatada}"
        driver.get(url_busca)
        time.sleep(1)

        # Seletor para os resultados no DuckDuckGo
        elementos = driver.find_elements(By.CSS_SELECTOR, "a.result__a") 
        
        for elem in elementos:
            link = elem.get_attribute("href")
            if link and link.startswith("http"):
                urls_encontradas.append(link)
    except Exception as e:
        st.warning(f"Ocorreu um erro ao buscar por '{query}': {e}")
        
    return urls_encontradas[:num_resultados]

# --- Interface do Usuário (sem alterações) ---
if 'resultados_df' not in st.session_state:
    st.session_state.resultados_df = None

input_text = st.text_area("Cole a lista de portais aqui (um por linha):", height=250, placeholder="Rádio Santana FM\nPortal Guaraciaba Notícias\nIpu Notícias...")

if st.button("🚀 Iniciar Busca com Opera"):
    if not input_text.strip():
        st.warning("Por favor, insira pelo menos um nome na lista.")
    else:
        # Lógica de busca e exibição... (continua igual ao código anterior)
        lista_de_buscas = [line.strip() for line in input_text.split('\n') if line.strip()]
        df_final = pd.DataFrame()
        with st.spinner("Aguarde... a busca com Opera está em andamento..."):
            driver = get_driver()
            status_text = st.empty()
            for i, nome_busca in enumerate(lista_de_buscas):
                status_text.info(f"Buscando por: '{nome_busca}' ({i+1}/{len(lista_de_buscas)})")
                resultados_gerais = realizar_busca(driver, f'"{nome_busca}"')
                if resultados_gerais:
                    for url in resultados_gerais:
                        dominio = urlparse(url).netloc.replace("www.", "")
                        nova_linha = pd.DataFrame([{"Fonte Pesquisada": nome_busca, "Site (Domínio)": dominio, "URL": url}])
                        df_final = pd.concat([df_final, nova_linha], ignore_index=True)
                else:
                    nova_linha = pd.DataFrame([{"Fonte Pesquisada": nome_busca, "Site (Domínio)": "N/A", "URL": "Nenhum resultado encontrado"}])
                    df_final = pd.concat([df_final, nova_linha], ignore_index=True)
            status_text.empty()
        st.success("✅ Busca finalizada com sucesso!")
        st.session_state.resultados_df = df_final

# --- Seção de Resultados (sem alterações) ---
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
