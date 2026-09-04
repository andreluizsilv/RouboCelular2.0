import logging
from typing import Dict, Tuple
from django.db.models import Avg, Q
from tqdm import tqdm
from ocorrencias.models import Endereco

logger = logging.getLogger(__name__)


def preencher_coordenadas_por_media_bairro() -> None:
    """Imputa coordenadas geográficas ausentes calculando a média espacial.

    Busca todos os registros de `EnderecoReferencia` que possuem `latitude`
    ou `longitude` nulas e atribui a eles o ponto médio geográfico dos
    vizinhos cadastrados.

    Estratégia de Fallback:
        1. Prioridade 1: Média calculada dentro do mesmo Bairro e Cidade.
        2. Prioridade 2: Média global da Cidade (caso o bairro não possua
           nenhum vizinho geocodificado).

    Side Effects:
        - Executa queries de agregação (`Avg`) na tabela `EnderecoReferencia`.
        - Realiza atualizações em lote via `bulk_update` com tamanho pré-definido.

    Returns:
        None
    """
    logger.info("Iniciando processo de imputação de coordenadas...")

    enderecos_sem_coords = Endereco.objects.filter(
        Q(latitude__isnull=True) | Q(longitude__isnull=True)
    )
    total_pendentes = enderecos_sem_coords.count()

    if total_pendentes == 0:
        logger.info("Nenhum endereço pendente de coordenadas.")
        return

    # 1. Agrupamento e Média por (Bairro, Cidade)
    medias_bairro = (
        Endereco.objects.filter(latitude__isnull=False, longitude__isnull=False)
        .values("bairro", "cidade")
        .annotate(lat_media=Avg("latitude"), long_media=Avg("longitude"))
    )

    mapa_bairro: Dict[Tuple[str, str], Tuple[float, float]] = {
        ((item["bairro"] or "").strip().upper(), (item["cidade"] or "").strip().upper()): (
            item["lat_media"],
            item["long_media"],
        )
        for item in medias_bairro
        if item["bairro"] and item["cidade"]
    }

    # 2. Agrupamento e Média por Cidade (Fallback)
    medias_cidade = (
        Endereco.objects.filter(latitude__isnull=False, longitude__isnull=False)
        .values("cidade")
        .annotate(lat_media=Avg("latitude"), long_media=Avg("longitude"))
    )

    mapa_cidade: Dict[str, Tuple[float, float]] = {
        (item["cidade"] or "").strip().upper(): (item["lat_media"], item["long_media"])
        for item in medias_cidade
        if item["cidade"]
    }

    lote_atualizacao = []
    tamanho_lote = 2000
    atualizados = 0

    for obj in tqdm(
        enderecos_sem_coords.iterator(chunk_size=tamanho_lote),
        total=total_pendentes,
        desc="🌐 Geocodificação Imputada (Média)",
        unit="end",
    ):
        bairro_norm = (obj.bairro or "").strip().upper()
        cidade_norm = (obj.cidade or "").strip().upper()

        chave_bairro = (bairro_norm, cidade_norm)
        coords = None

        if chave_bairro in mapa_bairro:
            coords = mapa_bairro[chave_bairro]
        elif cidade_norm in mapa_cidade:
            coords = mapa_cidade[cidade_norm]

        if coords:
            obj.latitude, obj.longitude = coords
            lote_atualizacao.append(obj)
            atualizados += 1

        if len(lote_atualizacao) >= tamanho_lote:
            Endereco.objects.bulk_update(
                lote_atualizacao, ["latitude", "longitude"], batch_size=tamanho_lote
            )
            lote_atualizacao = []

    if lote_atualizacao:
        Endereco.objects.bulk_update(
            lote_atualizacao, ["latitude", "longitude"], batch_size=tamanho_lote
        )

    logger.info(f"Sucesso: {atualizados}/{total_pendentes} endereços corrigidos com sucesso.")