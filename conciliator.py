from datetime import datetime
import pandas as pd
from dateutil import parser
from numpy import nan, isnan
from pandas import DataFrame
import difflib


class Conciliator():
    def __init__(self, df_bank: DataFrame, df_quickbook: DataFrame):
        self.validate_and_normalization(df_bank, df_quickbook)
        self.df_bank: DataFrame = df_bank
        self.df_quickbook: DataFrame = df_quickbook
        self.df_results = DataFrame
        

    def convert_amount(self, value, to_negative=False):
        try:
            s = str(value)
            if ',' in s and '.' not in s:
                s = s.replace(',', '.')
            elif ',' in s and '.' in s:
                s = s.replace(',', '')
            amount = round(float(s), 2)
            if isnan(amount):
                return nan
            return -abs(amount) if to_negative else amount
        except Exception as error:
            print(value, error)
            return None

    def is_negative(self, number):
        return number < 0



    def validate_and_normalization(self, df_bank: DataFrame, df_quickbook: DataFrame):
        payment_col = None
        for col in ['Payment (USD)', 'payment (USD)', 'Payment', 'payment']:
            if col in df_quickbook.columns:
                payment_col = col
                break
        
        deposit_col = None
        for col in ['Deposit (USD)', 'deposit (USD)', 'Deposit', 'deposit']:
            if col in df_quickbook.columns:
                deposit_col = col
                break

        expected_qb = {
            'Memo': 'descripción de la transacción',
            payment_col or 'Payment (USD)': 'créditos (salidas de dinero)',
            deposit_col or'Deposit (USD)': 'débitos (entradas de dinero)',
        }
        expected_bank = {
            'Amount': 'monto de la transacción',
            'Payee': 'descripción del beneficiario',
        }

        missing_qb = [col for col in expected_qb if col not in df_quickbook.columns]
        missing_bank = [col for col in expected_bank if col not in df_bank.columns]

        def sugerences(missings, current_columns):
            text_sugerences = ""
            for col in missings:
                similar = difflib.get_close_matches(col, current_columns, n=1, cutoff=0.6)
                if similar:
                    text_sugerences += f"   ¿Quizás quisiste decir '{similar[0]}' para '{col}'?\n"
            return text_sugerences

        if missing_qb:
            msg = "\n❌ Faltan columnas en el archivo QBO:\n"
            for col in missing_qb:
                msg += f" - '{col}': {expected_qb[col]}\n"
            msg += sugerences(missing_qb, df_quickbook.columns)
            msg += f"\nColumnas detectadas en QBO: {list(df_quickbook.columns)}"
            raise Exception(msg)

        if missing_bank:
            msg = "\n❌ Faltan columnas en el archivo BANCO:\n"
            for col in missing_bank:
                msg += f" - '{col}': {expected_bank[col]}\n"
            msg += sugerences(missing_bank, df_bank.columns)
            msg += f"\nColumnas detectadas en BANCO: {list(df_bank.columns)}"
            raise Exception(msg)

        # Normalización
        df_quickbook['description'] = df_quickbook['Memo']
        df_quickbook['credit'] = df_quickbook[payment_col].apply(
            lambda x: self.convert_amount(x, to_negative=True)
        )
        df_quickbook['debit'] = df_quickbook[deposit_col].apply(self.convert_amount)

        df_bank['amount'] = df_bank['Amount'].apply(self.convert_amount)
        df_bank['description'] = df_bank['Payee']

        # Validación de montos vacíos
        if df_bank['amount'].isna().any():
            raise Exception("El archivo BANCO contiene montos vacíos en la columna 'Amount'.")

        if df_quickbook['credit'].isna().all() and df_quickbook['debit'].isna().all():
            raise Exception("El archivo QBO no contiene valores válidos ni en 'Payment (USD)' ni en 'Deposit (USD)'.")

        self.normalize_date(df_bank)
        self.normalize_date(df_quickbook)


    def normalize_date(self, df:DataFrame   , col='Date'):
                
        df[col] = pd.to_datetime(df[col], infer_datetime_format=True, format='mixed').dt.strftime('%m/%d/%Y')
        df[col] = pd.to_datetime(df[col], infer_datetime_format=True, format='mixed').dt.strftime('%m/%d/%Y')
        return df


    def mark_invalid_quickbook(self, used_quickbook):
        invalids = []
        unused_quickbook = self.df_quickbook.loc[
            ~self.df_quickbook.index.isin(used_quickbook)
        ]

        for idx, row in unused_quickbook.iterrows():
            amount_col = 'credit' if self.is_negative(row.get('credit', 0)) else 'debit'
            invalids.append({
                'QB_Fecha': row["Date"],
                'QB_Desc': row.get('Memo', ''),
                'QB_amount': row[amount_col],
                'QB_status': 'INVALID',
                'Banco_Fecha': '',
                'Banco_Desc': '',
                'Banco_Monto': '',
                'Estado': ''
            })

        return invalids

    def conciliate(self):
        matches = []
        used_quickbook = set()

        for idx, row in self.df_bank.iterrows():
            amount = 'credit' if self.is_negative(row['amount']) else 'debit'

            coincidences = self.df_quickbook[
                (~self.df_quickbook[amount].isna()) &
                (self.df_quickbook[amount] == row['amount']) &
                (~self.df_quickbook.index.isin(used_quickbook))
            ]

            if pd.isna(row['amount']):
                raise Exception(
                    "\n\nEl archivo contiene algunos montos en blanco\n"
                    "asegúrate de haber descargado el archivo en xlsx\n"
                    "O llena estos espacios en blanco. (puedes usar un 0)"
                )

            if not coincidences.empty:
                mejor = coincidences.iloc[0]
                used_quickbook.add(mejor.name)
                matches.append({
                    'QB_Fecha': mejor["Date"],
                    'QB_Desc': mejor.get('Memo', ''),
                    'QB_amount': mejor[amount],
                    'QB_status': 'MATCH',
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
                    'QB_status': '',
                    'Banco_Fecha': row["Date"],
                    'Banco_Desc': row.get('Payee'),
                    'Banco_Monto': row['amount'],
                    'Estado': 'NO_MATCH'
                })

        
        matches.extend(self.mark_invalid_quickbook(used_quickbook))
        self.df_results = pd.DataFrame(matches)
        return self.df_results
    
    def get_bank_no_match_df(self):
        df_bank_copy = self.df_results.copy()
        df_bank_copy = df_bank_copy[df_bank_copy['Estado'] == 'NO_MATCH']
        df_bank_copy = df_bank_copy.drop(columns=['QB_Fecha', 'QB_Desc', 'QB_amount', 'QB_status'])
        return df_bank_copy
