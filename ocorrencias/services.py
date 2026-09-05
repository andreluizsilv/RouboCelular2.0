from datetime import timedelta
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import Count, F, Max, Q
from django.db.models.functions import ExtractHour
from django.utils import timezone

from .models import OcorrenciaCelular


class OcorrenciaFilterService:

    @staticmethod
    def obter_por_id(pk):
        return OcorrenciaCelular.objects.select_related('endereco').filter(pk=pk).first()

    @staticmethod
    def aplicar_filtros(params):
        qs = OcorrenciaCelular.objects.select_related('endereco').all()

        q = params.get('q', '').strip()
        tipo = params.get('tipo', 'tudo')

        # Full-Text Search (FTS) dinâmico sem conflito de nomes
        # Full-Text Search (FTS) dinâmico sem conflito de nomes
        if q:
            query = SearchQuery(q, config='portuguese')

            match tipo:
                case 'rua':
                    qs = qs.annotate(
                        rua_vec=SearchVector('endereco__logradouro', config='portuguese')
                    ).filter(rua_vec=query)

                case 'bairro':
                    qs = qs.annotate(
                        bairro_vec=SearchVector('endereco__bairro', config='portuguese')
                    ).filter(bairro_vec=query)

                case 'cidade':
                    qs = qs.annotate(
                        cidade_vec=SearchVector('endereco__cidade', config='portuguese')
                    ).filter(cidade_vec=query)

                case 'marca':
                    qs = qs.filter(marca_search_vector=query)

                case _:
                    qs = qs.filter(search_vector=query)

        # Filtros Exatos / Selects
        municipio = params.get('municipio')
        if municipio:
            qs = qs.filter(endereco__cidade=municipio)

        bairro = params.get('bairro')
        if bairro:
            qs = qs.filter(endereco__bairro=bairro)

        marca = params.get('marca')
        if marca:
            qs = qs.filter(marca_celular=marca)

        # Filtros por Intervalo de Data
        data_inicio = params.get('data_inicio')
        if data_inicio:
            qs = qs.filter(data_ocorrencia__gte=data_inicio)

        data_fim = params.get('data_fim')
        if data_fim:
            qs = qs.filter(data_ocorrencia__lte=data_fim)

        # Atalhos Predefinidos de Período
        periodo = params.get('periodo')
        if periodo:
            hoje = timezone.now().date()
            if periodo == '7d':
                qs = qs.filter(data_ocorrencia__gte=hoje - timedelta(days=7))
            elif periodo == '30d':
                qs = qs.filter(data_ocorrencia__gte=hoje - timedelta(days=30))
            elif periodo == 'este_ano':
                qs = qs.filter(data_ocorrencia__year=hoje.year)

        return qs


    @staticmethod
    def calcular_kpis(qs):
        total = qs.count()

        top_marca_qs = (
            qs.values('marca_celular')
            .annotate(total=Count('id'))
            .order_by('-total')
            .first()
        )
        marca_top = top_marca_qs['marca_celular'] if top_marca_qs and top_marca_qs['marca_celular'] else "N/A"
        marca_top_qtd = top_marca_qs['total'] if top_marca_qs else 0

        top_hora_qs = (
            qs.filter(hora_ocorrencia__isnull=False)
            .annotate(hora=ExtractHour('hora_ocorrencia'))
            .values('hora')
            .annotate(total=Count('id'))
            .order_by('-total')
            .first()
        )

        if top_hora_qs and top_hora_qs['hora'] is not None:
            hora_int = top_hora_qs['hora']
            horario_top = f"{hora_int:02d}:00h"
            horario_top_qtd = top_hora_qs['total']
        else:
            horario_top = "N/A"
            horario_top_qtd = 0

        return {
            'total_ocorrencias': total,
            'marca_top': marca_top,
            'marca_top_qtd': marca_top_qtd,
            'horario_top': horario_top,
            'horario_top_qtd': horario_top_qtd,
        }


    @staticmethod
    def obter_top_ruas(qs, limit=10):
        return list(
            qs.values(
                logradouro=F('endereco__logradouro'),
                bairro=F('endereco__bairro'),
                cidade=F('endereco__cidade')
            )
            .annotate(
                total=Count('id'),
                ultima_ocorrencia_id=Max('id')
            )
            .order_by('-total')[:limit]
        )


    @staticmethod
    def obter_distribuicao_marcas(qs, limit=10):
        return list(
            qs.values(marca=F('marca_celular'))
            .annotate(total=Count('id'))
            .order_by('-total')[:limit]
        )


    @staticmethod
    def obter_distribuicao_horarios(qs):
        return list(
            qs.filter(hora_ocorrencia__isnull=False)
            .annotate(hora=ExtractHour('hora_ocorrencia'))
            .values('hora')
            .annotate(total=Count('id'))
            .order_by('hora')
        )

    @staticmethod
    def obter_evolucao_temporal(qs):
        return list(
            qs.filter(data_ocorrencia__isnull=False)
            .values(data=F('data_ocorrencia'))
            .annotate(total=Count('id'))
            .order_by('data')
        )