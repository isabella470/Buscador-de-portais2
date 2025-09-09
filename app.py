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
st.set_page_config(page_title="Buscador e Extrator de HTML", page_icon="🔎", layout="wide")

st.title("🔎 Buscador de Portais e Extrator de HTML")
st.markdown("Cole uma lista de nomes, clique em 'Iniciar Busca'. Após os resultados aparecerem, escolha uma página para extrair seu código HTML.")

# --- Cache para o WebDriver ---
@st.cache_resource
def get_driver():
    """Inicializa e retorna o driver do Selenium, mantendo-o em cache."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def realizar_busca(driver, query, num_resultados=5):
    """Busca no Google e extrai os links dos resultados."""
    urls_encontradas = []
    try:
        query_formatada = query.replace(" ", "+")
        driver.get(f"https://www.google.com/search?q={query_formatada}&num={num_resultados}")
        time.sleep(2)

        elementos = driver.find_elements(By.CSS_SELECTOR, "a > h3")
        
        for elem in elementos:
            link = elem.find_element(By.XPATH, "..").get_attribute("href")
            if link and link.startswith("http"):
                urls_encontradas.append(link)

    except Exception as e:
        st.warning(f"Ocorreu um erro ao buscar por '{query}': {e}")
        
    return urls_encontradas[:num_resultados]

def extrair_html(driver, url):
    """Navega até uma URL e retorna o código-fonte HTML da página."""
    try:
        driver.get(url)
        time.sleep(3) # Pausa para permitir o carregamento de JavaScript
        return driver.page_source
    except Exception as e:
        return f"Não foi possível extrair o HTML da página {url}. Erro: {e}"

# --- Interface do Usuário ---

# Inicializa o session_state para guardar os resultados
if 'resultados_df' not in st.session_state:
    st.session_state['resultados_df'] = None

input_text = st.text_area("Cole a lista de portais aqui (um por linha):", height=200, placeholder="Portal Revista Acontece\nCariri News\nSobral News...")

if st.button("🚀 Iniciar Busca"):
    if not input_text.strip():
        st.warning("Por favor, insira pelo menos um nome na lista.")
    else:
        lista_de_buscas = [line.strip() for line in input_text.split('\n') if line.strip()]
        
        df_final = pd.DataFrame()
        
        with st.spinner("Aguarde... a busca está em andamento..."):
            driver = get_driver()
            status_text = st.empty()

            for i, nome_busca in enumerate(lista_de_buscas):
                status_text.info(f"Buscando por: '{nome_busca}' ({i+1}/{len(lista_de_buscas)})")
                
                query_portal = f'"{nome_busca}" site oficial'
                resultados_portal = realizar_busca(driver, query_portal, num_resultados=1)
                portal_principal = resultados_portal[0] if resultados_portal else "Não encontrado"
                
                query_geral = f'"{nome_busca}"'
                resultados_gerais = realizar_busca(driver, query_geral)
                
                if resultados_gerais:
                    for url in resultados_gerais:
                        dominio = urlparse(url).netloc.replace("www.", "")
                        nova_linha = pd.DataFrame([{
                            "Fonte Pesquisada": nome_busca,
                            "Portal Principal Sugerido": portal_principal,
                            "Site (Domínio)": dominio,
                            "URL": url
                        }])
                        df_final = pd.concat([df_final, nova_linha], ignore_index=True)
                else:
                    nova_linha = pd.DataFrame([{
                        "Fonte Pesquisada": nome_busca,
                        "Portal Principal Sugerido": portal_principal,
                        "Site (Domínio)": "N/A",
                        "URL": "Nenhum resultado encontrado"
                    }])
                    df_final = pd.concat([df_final, nova_linha], ignore_index=True)
            
            status_text.empty()

        st.success("✅ Busca finalizada!")
        # Armazena os resultados no session_state para evitar novas buscas
        st.session_state['resultados_df'] = df_final

# --- Seção de Resultados e Extração de HTML ---
if st.session_state['resultados_df'] is not in (None, 'DataFrame is empty'):
    
    st.subheader("Resultados da Busca")
    df_resultados = st.session_state['resultados_df']
    st.dataframe(df_resultados)

    # Botão para baixar o Excel com a lista de URLs
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_resultados.to_excel(writer, index=False, sheet_name='Resultados')
    
    st.download_button(
        label="📥 Baixar lista de URLs em Excel",
        data=output.getvalue(),
        file_name="resultados_buscas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("Extrair Código HTML de uma Página")
    
    # Cria uma lista de opções para o selectbox
    opcoes = [f"{row['Site (Domínio)']} - {row['URL']}" for index, row in df_resultados.iterrows() if row['URL'] != "Nenhum resultado encontrado"]
    
    if opcoes:
        url_selecionada_str = st.selectbox("Selecione uma página para extrair o HTML:", options=opcoes)
        
        if st.button("📄 Extrair HTML"):
            # Extrai a URL da string selecionada
            url_para_extrair = url_selecionada_str.split(' - ')[-1]

            with st.spinner(f"Navegando até {url_para_extrair} e extraindo conteúdo..."):
                driver = get_driver()
                html_content = extrair_html(driver, url_para_extrair)
                
                st.success("HTML extraído com sucesso!")
                # Exibe o código HTML em uma caixa de código
                st.code(html_content, language='html', line_numbers=True)
