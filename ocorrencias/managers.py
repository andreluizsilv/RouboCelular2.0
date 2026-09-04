from django.db import models
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


class OcorrenciaQuerySet(models.QuerySet):
    def buscar_fts(self, termo: str):
        """
        Executa a busca Full-Text Search com suporte ao idioma português,
        pesos de relevância por campo e ranqueamento (SearchRank).
        """
        if not termo:
            return self

        # Define os pesos dos campos: A (maior relevância) até C (menor)
        vector = (
                SearchVector('marca_celular', weight='A', config='portuguese') +
                SearchVector('num_bo', weight='A', config='portuguese') +
                SearchVector('endereco__logradouro', weight='B', config='portuguese') +
                SearchVector('endereco__bairro', weight='B', config='portuguese') +
                SearchVector('endereco__cidade', weight='C', config='portuguese') +
                SearchVector('delegacia_nome', weight='C', config='portuguese')
        )

        # Converte a string digitada pelo usuário em tokens de busca
        query = SearchQuery(termo, config='portuguese')

        return (
            self.annotate(rank=SearchRank(vector, query))
            .filter(rank__gte=0.01)
            .order_by('-rank')
        )

    def com_coordenadas(self):
        """
        Filtra apenas as ocorrências que possuem coordenadas válidas
        para uso nos mapas de calor/pins.
        """
        return self.filter(
            endereco__latitude__isnull=False,
            endereco__longitude__isnull=False
        )


class OcorrenciaManager(models.Manager):
    """
    Manager customizado que expõe a API do QuerySet para a aplicação.
    """

    def get_queryset(self):
        return OcorrenciaQuerySet(self.model, using=self._db)

    def buscar_fts(self, termo: str):
        return self.get_queryset().buscar_fts(termo)

    def com_coordenadas(self):
        return self.get_queryset().com_coordenadas()