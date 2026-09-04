from django.core.cache import cache
from .models import OcorrenciaCelular

class OcorrenciaFilterService:
    """
    Serviço centralizado para filtrar ocorrências.
    Atende tanto a Navbar Global quanto a Listagem e as APIs do Dashboard.
    """

    @classmethod
    def aplicar_filtros(cls, request_params):
        # 1. Carrega a consulta base otimizada com select_related (evita o problema N+1 queries)
        qs = OcorrenciaCelular.objects.select_related('endereco').all()

        # 2. Captura os parâmetros
        termo_busca = request_params.get('q', '').strip()
        tipo_busca = request_params.get('tipo', 'tudo')

        # 3. Executa a busca FTS via Manager ou buscas pontuais
        if termo_busca:
            if tipo_busca == 'marca':
                qs = qs.filter(marca_celular__icontains=termo_busca)
            elif tipo_busca == 'rua':
                qs = qs.filter(endereco__logradouro__icontains=termo_busca)
            elif tipo_busca == 'bairro':
                qs = qs.filter(endereco__bairro__icontains=termo_busca)
            elif tipo_busca == 'cidade':
                qs = qs.filter(endereco__cidade__icontains=termo_busca)
            else:
                qs = qs.buscar_fts(termo_busca)  # Método encapsulado no OcorrenciaManager

        # 4. Filtros secundários do Dashboard
        marca = request_params.get('marca')
        if marca:
            qs = qs.filter(marca_celular__iexact=marca)

        municipio = request_params.get('municipio')
        if municipio:
            qs = qs.filter(endereco__cidade__iexact=municipio)

        data_inicio = request_params.get('data_inicio')
        data_fim = request_params.get('data_fim')
        if data_inicio:
            qs = qs.filter(data_ocorrencia__gte=data_inicio)
        if data_fim:
            qs = qs.filter(data_ocorrencia__lte=data_fim)

        return qs


def get_opcoes_filtros():
    """Retorna listas em cache para preencher os elementos <select> do HTML."""
    marcas = cache.get_or_set(
        "lista_marcas",
        lambda: list(OcorrenciaCelular.objects.values_list('marca_celular', flat=True).distinct().order_by('marca_celular')),
        3600
    )
    municipios = cache.get_or_set(
        "lista_municipios",
        lambda: list(OcorrenciaCelular.objects.values_list('endereco__cidade', flat=True).distinct().order_by('endereco__cidade')),
        3600
    )
    return {
        'marcas': [m for m in marcas if m],
        'municipios': [mun for mun in municipios if mun],
    }