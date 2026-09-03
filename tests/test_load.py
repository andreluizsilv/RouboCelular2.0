import pandas as pd
from django.test import TestCase
from ocorrencias.models import EnderecoReferencia, OcorrenciaCelular
from etl.load import carregar_no_banco


class TestLoad(TestCase):
    def setUp(self):
        self.df_mock = pd.DataFrame({
            "NUM_BO": [1001, 1001, 1002],
            "ANO_BO": [2026, 2026, 2026],
            "DATA_OCORRENCIA": ["2026-01-10", "2026-01-10", "2026-01-11"],
            "HORA_OCORRENCIA": ["12:00", "12:00", "15:30"],
            "LOGRADOURO": ["AV PAULISTA", "AV PAULISTA", "RUA AUGUSTA"],
            "BAIRRO": ["BELA VISTA", "BELA VISTA", "CONSOLACAO"],
            "CIDADE": ["SAO PAULO", "SAO PAULO", "SAO PAULO"],
            "DELEGACIA_NOME": ["01 DP", "01 DP", "04 DP"],
            "MARCA_CELULAR": ["APPLE", "SAMSUNG", "MOTOROLA"],
            "LATITUDE": [-23.5614, -23.5614, -23.5522],
            "LONGITUDE": [-46.6558, -46.6558, -46.6583],
        })

    def test_carregar_no_banco(self):
        carregar_no_banco(self.df_mock)

        # Garante criação de 2 endereços únicos
        self.assertEqual(EnderecoReferencia.objects.count(), 2)

        # Garante deduplicação de BO repetido na mesma delegacia (1001 inserido apenas 1 vez)
        self.assertEqual(OcorrenciaCelular.objects.count(), 2)

        # Valida vínculo da chave estrangeira
        ocorrencia = OcorrenciaCelular.objects.get(num_bo=1001)
        self.assertEqual(ocorrencia.endereco.logradouro, "AV PAULISTA")