import io
import streamlit as st
import pandas as pd
from conciliator import Conciliator
import psutil, time, os


if not st.session_state.get('show_results', False):
    st.title("Click Click - Conciliador Bancario")
    st.warning("La columna DATE del archivo QBO y BANCO debe estar organizada mm/dd/yyyy", icon="⚠️")
    file_bank = st.file_uploader("Sube el archivo del BANCO", type=["csv", "xlsx"])
    file_qb = st.file_uploader("Sube el archivo de QUICKBOOKS", type=["csv", "xlsx"])

    if file_bank and file_qb:
        conciliar_clicked = st.button("Conciliar")
        if conciliar_clicked:
            try:
                start = time.time()
                process = psutil.Process(os.getpid())
                if file_bank.name.endswith(".csv"):
                    df_bank = pd.read_csv(file_bank, dtype={"Date": str})
                else:
                    df_bank = pd.read_excel(file_bank, dtype={"Date": str})

                if file_qb.name.endswith(".csv"):
                    df_quickbook = pd.read_csv(file_qb, dtype={"Date": str})
                else:
                    df_quickbook = pd.read_excel(file_qb, dtype={"Date": str})

                conciliator = Conciliator(df_bank, df_quickbook)
                result = conciliator.conciliate()
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    result.to_excel(writer, index=False, sheet_name='Conciliacion')
                output.seek(0)

                csv_final_file = io.BytesIO()
                csv_final_file.write(conciliator.get_bank_no_match_df().to_csv(index=False).encode('utf-8'))
                csv_final_file.seek(0)

                st.session_state['result'] = result
                st.session_state['output'] = output.getvalue()
                st.session_state['csv_final_file'] = csv_final_file.getvalue()
                st.session_state['show_results'] = True
                st.rerun()
            except Exception as error:
                st.warning(error, icon="⚠️")

if st.session_state.get('show_results', False):
    st.write("Resultados de la conciliación:")
    st.dataframe(st.session_state['result'])
    st.download_button(
        label="Descargar resultado de comparativa",
        data=st.session_state['output'],
        file_name="resultados_conciliacion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.subheader('', divider='blue')
    st.subheader("Transferencias bancarias sin coincidencias.")
    st.info("Archivo csv con las transacciones bancarias no registradas " +
            "en quickbook (transferencias con status 'No match')")
    
    col_1, _, col_3 = st.columns([2, 1, 1])
    with col_1:
        st.download_button(
            label="Descargar transferencias sin coincidencias",
            data=st.session_state['csv_final_file'],
            file_name="resultado_transferencias_sin_coincidencias.csv",
            mime="text/csv",
        )
    with col_3:
        if st.button("Nueva conciliacion"):
            st.session_state.clear()
            st.rerun()



