# Conteúdo ATUALIZADO para o seu arquivo app.py

import streamlit as st
import pandas as pd
import time
from googlesearch import search
import io

# --- Função Auxiliar (sem mudanças) ---
def to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    processed_data = output.getvalue()
    return processed_data

# --- Interface da Aplicação (sem mudanças) ---
st.set_page_config(page_title="Buscador de Sites", page_icon="🌐")

st.title("🌐 Buscador de Sites de Portais")
st.markdown("""
Esta ferramenta automatiza a busca por sites de veículos de comunicação.
**Como usar:**
1. Prepare um arquivo Excel com as colunas `nome` e `regiao`.
2. Faça o upload do arquivo abaixo.
3. Clique em **"Iniciar Busca"** e aguarde o processo.
4. Ao final, os resultados aparecerão na tela e um botão para download será disponibilizado.
""")

uploaded_file = st.file_uploader(
    "Faça o upload do seu arquivo Excel aqui",
    type=['xlsx']
)

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("Arquivo carregado com sucesso! Abaixo uma prévia dos dados:")
        st.dataframe(df.head())

        if st.button("🚀 Iniciar Busca de Sites", type="primary"):
            lista_sites_encontrados = []
            total_rows = len(df)
            progress_bar = st.progress(0, text="Iniciando...")
            status_text = st.empty()

            for index, row in df.iterrows():
                # --- INÍCIO DA MUDANÇA IMPORTANTE ---
                try:
                    nome = str(row['nome'])
                    regiao = str(row.get('regiao', ''))
                    query = f"{nome} {regiao} portal de notícias site oficial"
                    
                    progress_text = f"Buscando por: {nome}... ({index + 1}/{total_rows})"
                    status_text.text(progress_text)
                    progress_bar.progress((index + 1) / total_rows, text=progress_text)

                    # Bloco de busca agora está dentro de um try/except
                    search_result = search(query, num_results=1, lang='pt-br', sleep_interval=5) # Aumentamos o intervalo para 5s
                    
                    if search_result:
                        primeiro_link = search_result[0]
                        lista_sites_encontrados.append(primeiro_link)
                    else:
                        lista_sites_encontrados.append("Não encontrado")
                
                except Exception as e:
                    # Se qualquer erro acontecer na busca, o código abaixo será executado
                    error_message = f"Erro na busca por '{nome}'. Motivo: {e}"
                    st.error(error_message) # Mostra o erro em vermelho na tela
                    lista_sites_encontrados.append("Falha na busca")
                    # O loop continua para o próximo item em vez de quebrar
                
                # --- FIM DA MUDANÇA IMPORTANTE ---
                
                # Pausa para não sobrecarregar o Google (já incluída no search)

            status_text.success("✅ Busca concluída!")
            df['Site_Encontrado'] = lista_sites_encontrados
            st.session_state.final_df = df

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo Excel: {e}")
        st.warning("Verifique se o arquivo Excel está no formato correto e se as colunas 'nome' e 'regiao' existem.")

if 'final_df' in st.session_state:
    st.markdown("---")
    st.subheader("Resultados da Busca")
    final_df = st.session_state.final_df
    st.dataframe(final_df)
    excel_bytes = to_excel_bytes(final_df)
    st.download_button(
        label="📥 Baixar Resultados em Excel",
        data=excel_bytes,
        file_name="sites_encontrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
