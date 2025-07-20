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

def conciliar(df_banco, df_qb):
    # Normalizar columnas
    try:
        df_qb['credit'] = df_qb['Payment (USD)'].apply(lambda x: convert_amount(x, to_negative=True))
    except:
        raise Exception("La columna de QBO que contiene el credito, debe llamarse: Payment (USD)")
    
    try:
        df_qb['debit'] = df_qb['Deposit (USD)'].apply(convert_amount)
    except:
        raise Exception("La columna de QBO que contiene el debito, debe llamarse: Deposit (USD)")

    try:
        df_banco['amount'] = df_banco['Amount'].apply(convert_amount)
    except:
        raise Exception("La columna del monto en el Banco debe llamarse:  Amount")



    matches = []
    usados_qb = set()

    for idx, row in df_banco.iterrows():
        amount = 'credit' if is_negative(row['amount']) else 'debit'

        coincidencias = df_qb[
            (~df_qb[amount].isna()) &
            (df_qb[amount] == row['amount']) &
            (~df_qb.index.isin(usados_qb))
        ]

        if row["Description"].startswith("Zelle Transfer") and pd.isna(row['amount']):
            raise Exception(f"La fila {idx}, en BANCO no tiene amount. Llenalo o pon un valor de 0.")

        if not coincidencias.empty:
            mejor = coincidencias.iloc[0]
            usados_qb.add(mejor.name)
            matches.append({
                'QB_Fecha': mejor['Date'],
                'QB_Desc': mejor.get('Memo', ''),
                'QB_amount': mejor[amount],
                'Banco_Fecha': row['Date'],
                'Banco_Desc': row.get('Description', ''),
                'Banco_Monto': row['amount'],
                'Estado': 'MATCH'
            })
        else:
            matches.append({
                'QB_Fecha': '',
                'QB_Desc': '',
                'QB_amount': '',
                'Banco_Fecha': row['Date'],
                'Banco_Desc': row.get('Description', ''),
                'Banco_Monto': row['amount'],
                'Estado': 'NO_MATCH'
            })

    return pd.DataFrame(matches)
# Exportar resultado