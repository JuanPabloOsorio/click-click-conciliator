import datetime
import pandas as pd
from numpy import nan, isnan

def convert_amount(valor, to_negative=False):
    try:
        s = str(valor)
        if ',' in s and '.' not in s:
            s = s.replace(',', '.')
        elif ',' in s and '.' in s:
            s = s.replace(',', '')
        amount = round(float(s), 2)
        if isnan(amount):
            return nan
        return -abs(amount) if to_negative else amount
    except Exception as error:
        print(valor, error)
        return None

def is_negative(number):
    return number < 0

def remove_leading_zeros(date_str):
    parts = date_str.split('/')
    if len(parts) == 3:
        month = str(int(parts[0])) # Convert to int, then back to str to remove leading zero
        day = str(int(parts[1]))
        year = parts[2]
        return f"{month}/{day}/{year}"
    return date_str # Return original if not in expected format


def conciliar(df_banco, df_qb):

    try:
        df_qb['description'] = df_qb['Memo'].apply(lambda x: convert_amount(x, to_negative=True))
    except:
        raise Exception("La columna del archivo QBO que contiene la descripcion, debe llamarse: Memo")
    # Normalizar columnas
    try:
        df_qb['credit'] = df_qb['Payment (USD)'].apply(lambda x: convert_amount(x, to_negative=True))
    except:
        raise Exception("La columna del archivo QBO que contiene el credito, debe llamarse: Payment (USD)")
    
    try:
        df_qb['debit'] = df_qb['Deposit (USD)'].apply(convert_amount)
    except:
        raise Exception("La columna del archivo QBO que contiene el debito, debe llamarse: Deposit (USD)")

    try:
        df_banco['amount'] = df_banco['Amount'].apply(convert_amount)
    except:
        raise Exception("La columna del monto en archivo BANCO debe llamarse:  Amount")

    try:
        df_banco['description'] = df_banco['Payee'].apply(lambda x: convert_amount(x, to_negative=True))
    except:
        raise Exception("La columna del archivo BANCO que contiene la descripcion, debe llamarse: Payee")
    
    #Normalize Dates
# Forzar conversión sin ambigüedad
    df_qb["Date"] = pd.to_datetime(df_qb['Date'], infer_datetime_format=True, format='mixed').dt.strftime('%m/%d/%Y')
    df_banco["Date"] = pd.to_datetime(df_banco['Date'], infer_datetime_format=True, format='mixed').dt.strftime('%m/%d/%Y')

    matches = []
    usados_qb = set()

    for idx, row in df_banco.iterrows():
        amount = 'credit' if is_negative(row['amount']) else 'debit'

        coincidencias = df_qb[
            (~df_qb[amount].isna()) &
            (df_qb[amount] == row['amount']) &
            (~df_qb.index.isin(usados_qb))
        ]

        if pd.isna(row['amount']):
            raise Exception(f"\n\nEl archivo contiene algunos montos en blanco\n" +
                            "asegurate de haber descargado el archivo en xlsx\n" +
                            "O llena estos espacios en blanco. (puedes usar un 0)")


        if not coincidencias.empty:
            mejor = coincidencias.iloc[0]
            usados_qb.add(mejor.name)
            matches.append({
                'QB_Fecha': mejor["Date"],
                'QB_Desc': mejor.get('Memo', ''),
                'QB_amount': mejor[amount],
                'Banco_Fecha': row["Date"],
                'Banco_Desc': row.get('Payee'),
                'Banco_Monto': row['amount'],
                'Estado': 'MATCH'
            })
        else:
            matches.append({
                'QB_Fecha': '',
                'QB_Desc': '',
                'QB_amount': '',
                'Banco_Fecha': row["Date"],
                'Banco_Desc': row.get('Payee'),
                'Banco_Monto': row['amount'],
                'Estado': 'NO_MATCH'
            })

    return pd.DataFrame(matches)
# Exportar resultado