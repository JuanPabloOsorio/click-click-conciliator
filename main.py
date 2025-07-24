import io
import streamlit as st
import pandas as pd
from conciliator import Conciliator


st.title("Click Click - Conciliador Bancario")
st.warning("La columna DATE del archivo QBO y BANCO debe estar organizada mm/dd/yyyy", icon="⚠️")
file_bank = st.file_uploader("Sube el archivo del BANCO", type=["csv", "xlsx"])
file_qb = st.file_uploader("Sube el archivo de QUICKBOOKS", type=["csv", "xlsx"])

if file_bank and file_qb:
    if file_bank.name.endswith(".csv"):
        df_bank = pd.read_csv(file_bank, dtype={"Date": str})
    else:
        df_bank = pd.read_excel(file_bank, dtype={"Date": str})

    if file_qb.name.endswith(".csv"):
        df_quickbook = pd.read_csv(file_qb, dtype={"Date": str})
    else:
        df_quickbook = pd.read_excel(file_qb, dtype={"Date": str})

    if st.button("Conciliar"):
        try:
            conciliator = Conciliator(df_bank, df_quickbook)
            result = conciliator.conciliate()
            st.write("Resultados de la conciliación:")
            st.dataframe(result)
                    # Crear archivo en memoria
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                result.to_excel(writer, index=False, sheet_name='Conciliacion')
            output.seek(0)
            
            csv_final_file = io.BytesIO()
            csv_final_file.write(conciliator.get_bank_no_match_df().to_csv(index=False).encode('utf-8'))
            csv_final_file.seek(0)

            # Download button
            st.download_button(
                label="Descargar resultado de comparativa",
                data=output,
                file_name="resultados_conciliacion.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            st.subheader('', divider='blue')
            st.subheader("Transferencias bancarias sin coincidencias.")
            st.info("Archivo csv con las transacciones bancarias no registradas " +
            "en quickbook (transferencias con status 'No match')")

            st.download_button(
                label="Descargar transferencias sin coincidencias",
                data=csv_final_file,
                file_name="resultado_transferencias_sin_coincidencias.csv",
                mime="text/csv",
            )
        except Exception as error:
            st.warning(error, icon="⚠️")
        


