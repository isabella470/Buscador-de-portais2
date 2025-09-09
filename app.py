import streamlit as st
import pandas as pd
import time
import io
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# --- Configuração da Página do Streamlit ---
st.set_page_config(page_title="Buscador de Portais", page_icon="🔎", layout="wide")

st.title("🔎 Buscador Automatizado de Portais e Sites")
st.markdown("Cole uma lista de nomes (um por linha) e a ferramenta buscará os links principais no Google.")

# --- Cache para o WebDriver ---
@st.cache_resource
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# --- FUNÇÃO DE BUSCA ATUALIZADA ---
def realizar_busca(driver, query, num_resultados=5):
    """Função para buscar no Google e extrair links usando um seletor mais robusto."""
    urls_encontradas = []
    try:
        query_formatada = query.replace(" ", "+")
        # Adicionando &hl=pt-br para forçar resultados em português do Brasil
        url_busca = f"https://www.google.com/search?q={query_formatada}&num={num_resultados}&hl=pt-br"
        driver.get(url_busca)
        time.sleep(2)

        # NOVO SELETOR: Procura por divs que geralmente contêm os resultados da busca
        # e então pega o primeiro link (a) dentro deles.
        elementos = driver.find_elements(By.CSS_SELECTOR, "div.g") 
        
        if not elementos:
            # Se o primeiro seletor falhar, tenta um alternativo.
            st.warning(f"Seletor principal 'div.g' não encontrou resultados para '{query}'. Tentando seletor alternativo...")
            elementos = driver.find_elements(By.CSS_SELECTOR, "div[data-ved]")

        for elem in elementos:
            try:
                # Tenta encontrar o link dentro do elemento
                link = elem.find_element(By.TAG_NAME, "a").get_attribute("href")
                if link and link.startswith("http"):
                    urls_encontradas.append(link)
            except:
                # Se um 'div.g' não tiver um link (ex: "As pessoas também perguntam"), ignora e continua
                continue

    except Exception as e:
        st.warning(f"Ocorreu um erro ao buscar por '{query}': {e}")
        # Tenta salvar uma captura de tela para depuração (útil se estiver rodando localmente)
        # Em um app deployed, isso não será visível, mas pode ajudar a diagnosticar.
        try:
            driver.save_screenshot("debug_screenshot.png")
        except:
            pass
        
    return urls_encontradas[:num_resultados]

# --- Interface do Usuário (sem alterações) ---
if 'resultados_df' not in st.session_state:
    st.session_state.resultados_df = None

input_text = st.text_area("Cole a lista de portais aqui (um por linha):", height=250, placeholder="Rádio Santana FM\nPortal Guaraciaba Notícias\nIpu Notícias...")

if st.button("🚀 Iniciar Busca"):
    if not input_text.strip():
        st.warning("Por favor, insira pelo menos um nome na lista.")
    else:
        lista_de_buscas = [line.strip() for line in input_text.split('\n') if line.strip()]
        
        df_final = pd.DataFrame()
        
        with st.spinner("Aguarde... a busca está em andamento. Isso pode levar alguns minutos..."):
            driver = get_driver()
            status_text = st.empty()

            for i, nome_busca in enumerate(lista_de_buscas):
                status_text.info(f"Buscando por: '{nome_busca}' ({i+1}/{len(lista_de_buscas)})")
                
                query_portal = f'"{nome_busca}" site oficial'
                resultados_portal = realizar_busca(driver, query_portal, num_resultados=1)
                portal_principal = resultados_portal[0] if resultados_portal else "Não encontrado"
                
                query_geral = f'"{nome_busca}"'
                resultados_gerais = realizar_busca(driver, query_geral, num_resultados=5)
                
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
