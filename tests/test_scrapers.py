import os
import unittest
import pandas as pd
from etl.transform import processar_transformacao


class TestTransform(unittest.TestCase):
    def setUp(self):
        # 1. Cria o DataFrame com dados de teste
        self.raw_data = pd.DataFrame({
            'NUM_BO': [123, 124],
            'ANO_BO': [2026, 2026],
            'DATA_OCORRENCIA': ['2026-01-01', '2026-01-02'],
            'HORA_OCORRENCIA': ['10:00', '11:00'],
            'DESCR_PERIODO': ['MANHA', 'MANHA'],
            'RUBRICA': ['Furto', 'Roubo'],
            'DESCR_CONDUTA': ['Passageiro', 'Transeunte'],
            'DESCR_TIPOLOCAL': ['Via Publica', 'Via Publica'],
            'MARCA_CELULAR': ['Apple', 'Samsung'],
            'LOGRADOURO': ['Rua A', 'Rua B'],
            'BAIRRO': ['Centro', 'Jardins'],
            'CIDADE': ['SAO PAULO', 'SAO PAULO'],
            'CEP': [12345678, 87654321],
            'DELEGACIA_NOME': ['01 DP', '02 DP'],
            'LATITUDE': [-23.55, -23.56],
            'LONGITUDE': [-46.63, -46.64],
            'COLUNA_INUTIL': ['Lixo 1', 'Lixo 2']  # Coluna que deve ser descartada
        })

        # 2. Salva um arquivo Excel temporário para o teste ler
        self.caminho_temp = "tests/temp_test_input.xlsx"
        os.makedirs("tests", exist_ok=True)
        with pd.ExcelWriter(self.caminho_temp, engine='openpyxl') as writer:
            self.raw_data.to_excel(writer, sheet_name="CELULAR_2026", index=False)

    def tearDown(self):
        # 3. Limpa o arquivo temporário após o teste
        if os.path.exists(self.caminho_temp):
            os.remove(self.caminho_temp)

    def test_colunas_mantidas(self):
        df_tratado = processar_transformacao(self.caminho_temp, nome_aba="CELULAR_2026")

        # Assegura que a coluna desnecessária foi removida
        self.assertNotIn('COLUNA_INUTIL', df_tratado.columns)
        self.assertIn('NUM_BO', df_tratado.columns)
        self.assertEqual(len(df_tratado), 2)