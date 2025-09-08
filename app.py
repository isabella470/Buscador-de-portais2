import streamlit as st
import pandas as pd
import time
# from googlesearch import search  <- DESATIVADO PARA TESTE
import io

# --- Função Auxiliar (sem mudanças) ---
def to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    processed_data = output.getvalue()
    return processed_data

# --- Interface da Aplicação (título com v2 para confirmar a atualização) ---
st.set_page_config(page_title="Buscador de Sites", page_icon="🌐")

st.title("🌐 Buscador de Sites de Portais (v2)") # Mantemos o v2 para saber que atualizou
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
                nome = str(row['nome'])
                progress_text = f"Processando: {nome}... ({index + 1}/{total_rows})"
                status_text.text(progress_text)
                progress_bar.progress((index + 1) / total_rows, text=progress_text)

                # --- PARTE DA BUSCA FOI DESATIVADA ---
                # Em vez de buscar, apenas adicionamos uma mensagem de teste
                lista_sites_encontrados.append("Busca desativada para teste")
                time.sleep(0.1) # Pequena pausa para simular processamento
                
            status_text.success("✅ Processamento de teste concluído!")
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
