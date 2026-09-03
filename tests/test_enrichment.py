from django.test import TestCase
from ocorrencias.models import EnderecoReferencia
from etl.enrichment import preencher_coordenadas_por_media_bairro


class TestEnrichment(TestCase):
    def setUp(self):
        # Endereços com coordenadas conhecidas no mesmo bairro
        EnderecoReferencia.objects.create(
            logradouro="RUA A", bairro="CENTRO", cidade="SAO PAULO", uf="SP",
            latitude=-23.550000, longitude=-46.630000
        )
        EnderecoReferencia.objects.create(
            logradouro="RUA B", bairro="CENTRO", cidade="SAO PAULO", uf="SP",
            latitude=-23.560000, longitude=-46.640000
        )
        # Endereço sem coordenadas para ser corrigido
        self.end_sem_coord = EnderecoReferencia.objects.create(
            logradouro="RUA C", bairro="CENTRO", cidade="SAO PAULO", uf="SP",
            latitude=None, longitude=None
        )

    def test_preencher_coordenadas_por_media_bairro(self):
        preencher_coordenadas_por_media_bairro()
        self.end_sem_coord.refresh_from_db()

        self.assertIsNotNone(self.end_sem_coord.latitude)
        self.assertIsNotNone(self.end_sem_coord.longitude)
        self.assertAlmostEqual(self.end_sem_coord.latitude, -23.555000, places=5)
        self.assertAlmostEqual(self.end_sem_coord.longitude, -46.635000, places=5)