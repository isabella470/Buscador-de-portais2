import streamlit as st
import pandas as pd
import time
import io
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuração da Página do Streamlit ---
st.set_page_config(page_title="Buscador de Portais", page_icon="🔎", layout="wide")

st.title("🔎 Buscador Automatizado de Portais e Sites")
st.markdown("Cole uma lista de nomes (um por linha) e a ferramenta buscará os links principais no Google.")

# --- Cache para o WebDriver ---
# Isso evita que o WebDriver seja reinstalado a cada ação na página, melhorando a performance.
@st.cache_resource
def get_driver_service():
    # Opções do Selenium para rodar em ambiente de servidor (como o Streamlit Cloud)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Roda o navegador em segundo plano
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Instala e gerencia o ChromeDriver automaticamente
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def realizar_busca(driver, query, num_resultados=5):
    """Função para buscar no Google e extrair links usando Selenium."""
    urls_encontradas = []
    try:
        # Codifica a query para ser usada na URL do Google
        query_formatada = query.replace(" ", "+")
        driver.get(f"https://www.google.com/search?q={query_formatada}&num={num_resultados}")
        time.sleep(2)  # Espera a página carregar

        # Encontra os elementos que contêm os links dos resultados
        elementos = driver.find_elements(By.CSS_SELECTOR, "a > h3")
        
        for elem in elementos:
            link = elem.find_element(By.XPATH, "..").get_attribute("href")
            if link and link.startswith("http"):
                urls_encontradas.append(link)

    except Exception as e:
        st.warning(f"Ocorreu um erro ao buscar por '{query}': {e}")
        
    return urls_encontradas[:num_resultados]

# --- Interface do Usuário ---

# Área para o usuário colar a lista de jornais/fontes
input_text = st.text_area("Cole a lista de portais aqui (um por linha):", height=250, placeholder="Portal Revista Acontece\nCariri News\nSobral News...")

if st.button("🚀 Iniciar Busca"):
    if input_text.strip() == "":
        st.warning("Por favor, insira pelo menos um nome na lista.")
    else:
        # Processa a lista de entrada
        lista_de_buscas = [line.strip() for line in input_text.split('\n') if line.strip()]
        
        df_final = pd.DataFrame()
        
        # Inicia o spinner de carregamento
        with st.spinner("Aguarde... a busca está em andamento. Isso pode levar alguns minutos..."):
            driver = get_driver_service()
            status_text = st.empty() # Placeholder para mensagens de progresso

            for i, nome_busca in enumerate(lista_de_buscas):
                status_text.info(f"Buscando por: '{nome_busca}' ({i+1}/{len(lista_de_buscas)})")
                
                # Busca pelo "portal principal"
                query_portal = f'"{nome_busca}" site oficial'
                resultados_portal = realizar_busca(driver, query_portal, num_resultados=1)
                portal_principal = resultados_portal[0] if resultados_portal else "Não encontrado"
                
                # Busca por outras URLs
                query_geral = f'"{nome_busca}"'
                resultados_gerais = realizar_busca(driver, query_geral, num_resultados=5)
                
                # Monta um DataFrame temporário
                resultados_para_df = []
                if resultados_gerais:
                    for url in resultados_gerais:
                        dominio = urlparse(url).netloc.replace("www.", "")
                        resultados_para_df.append({
                            "Fonte Pesquisada": nome_busca,
                            "Portal Principal Sugerido": portal_principal,
                            "Site (Domínio)": dominio,
                            "URL": url
                        })
                else:
                    resultados_para_df.append({
                        "Fonte Pesquisada": nome_busca,
                        "Portal Principal Sugerido": portal_principal,
                        "Site (Domínio)": "N/A",
                        "URL": "Nenhum resultado encontrado"
                    })
                
                df_temp = pd.DataFrame(resultados_para_df)
                df_final = pd.concat([df_final, df_temp], ignore_index=True)

            status_text.empty() # Limpa a mensagem de progresso

        st.success("✅ Busca finalizada com sucesso!")
        
        # --- Exibe os resultados e oferece o download ---
        st.dataframe(df_final)

        # Prepara o arquivo Excel para download em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final.to_excel(writer, index=False, sheet_name='Resultados')
        
        st.download_button(
            label="📥 Baixar resultados em Excel",
            data=output.getvalue(),
            file_name="resultados_buscas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
