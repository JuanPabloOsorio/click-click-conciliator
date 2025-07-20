import io
import streamlit as st
import pandas as pd
from conciliador import conciliar


st.title("Click Click - Conciliador Bancario")

archivo_banco = st.file_uploader("Sube el archivo del BANCO", type=["csv", "xlsx"])
archivo_qb = st.file_uploader("Sube el archivo de QUICKBOOKS", type=["csv", "xlsx"])

if archivo_banco and archivo_qb:
    if archivo_banco.name.endswith(".csv"):
        df_banco = pd.read_csv(archivo_banco)
    else:
        df_banco = pd.read_excel(archivo_banco)

    if archivo_qb.name.endswith(".csv"):
        df_qb = pd.read_csv(archivo_qb)
    else:
        df_qb = pd.read_excel(archivo_qb)

    if st.button("Conciliar"):
        try:
            resultado = conciliar(df_banco, df_qb)
            st.write("Resultados de la conciliación:")
            st.dataframe(resultado)
                    # Crear archivo en memoria
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                resultado.to_excel(writer, index=False, sheet_name='Conciliacion')
            output.seek(0)

            # Botón de descarga
            st.download_button(
                label="Descargar resultado",
                data=output,
                file_name="resultado_conciliado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as error:
            st.warning(error, icon="⚠️")
        


