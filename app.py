# --- CÓDIGO FINAL E SIMPLIFICADO (v7 - Requests) ---

import streamlit as st
import time
import requests
from bs4 import BeautifulSoup
import io
import csv
import urllib.parse

# --- Nova Função de Busca (mais estável) ---
def buscar_link_portal(nome_portal):
    """
    Busca no Google usando requests e beautifulsoup para encontrar o primeiro link.
    """
    try:
        query = urllib.parse.quote_plus(f"{nome_portal} site oficial")
        url = f"https://www.google.com/search?q={query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Gera erro se a requisição falhar (ex: 429)

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Este seletor busca pelo link dentro da principal divisão de resultados do Google
        result_tag = soup.select_one("div.yuRUbf > a")
        
        if result_tag and result_tag.has_attr('href'):
            return result_tag['href']
        else:
            return "Link não encontrado."
            
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return "ERRO: Google bloqueou por excesso de buscas."
        return f"ERRO de HTTP: {e}"
    except Exception as e:
        return f"ERRO inesperado: {e}"

# --- Função para gerar um arquivo CSV para download (sem mudanças) ---
def to_csv_string(lista_de_dados):
    output = io.StringIO()
    if not lista_de_dados: return ""
    headers = lista_de_dados[0].keys()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(lista_de_dados)
    return output.getvalue()

# --- Interface da Aplicação ---
st.set_page_config(page_title="Buscador de Sites", page_icon="🌐")
st.title("🌐 Buscador de Sites Simples (v7 - Requests)")
st.markdown("Esta ferramenta usa um método de busca direto para encontrar sites de portais a partir de um arquivo .txt.")

uploaded_file = st.file_uploader(
    "Faça o upload do seu arquivo .txt (formato: nome,regiao)",
    type=['txt']
)

if uploaded_file is not None:
    try:
        string_data = uploaded_file.getvalue().decode('utf-8')
        reader = csv.DictReader(io.StringIO(string_data))
        lista_de_veiculos = list(reader)
        
        st.success(f"Arquivo '{uploaded_file.name}' carregado com sucesso!")
        st.write(f"Encontrados {len(lista_de_veiculos)} veículos para pesquisar.")

        if st.button("🚀 Iniciar Busca Simples", type="primary"):
            resultados_finais = []
            total_rows = len(lista_de_veiculos)
            progress_bar = st.progress(0, text="Iniciando...")
            status_text = st.empty()

            for index, veiculo in enumerate(lista_de_veiculos):
                nome = veiculo.get('nome', '')
                
                progress_text = f"Buscando por: {nome}... ({index + 1}/{total_rows})"
                status_text.text(progress_text)
                progress_bar.progress((index + 1) / total_rows, text=progress_text)

                # Chama a nova função de busca
                resultado_link = buscar_link_portal(nome)
                veiculo['Site_Encontrado'] = resultado_link
                
                resultados_finais.append(veiculo)

                # Pausa de segurança OBRIGATÓRIA para evitar bloqueio
                if index < total_rows - 1:
                    status_text.info(f"Pausa de 7s para evitar bloqueio... Próximo: item {index + 2}/{total_rows}")
                    time.sleep(7)

            status_text.success("✅ Busca concluída!")
            st.session_state.final_data = resultados_finais

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

if 'final_data' in st.session_state:
    st.markdown("---")
    st.subheader("Resultados da Busca")
    final_data = st.session_state.final_data
    st.dataframe(final_data)
    
    csv_string = to_csv_string(final_data)
    
    st.download_button(
        label="📥 Baixar Resultados em CSV",
        data=csv_string,
        file_name="sites_encontrados.csv",
        mime="text/csv"
    )
