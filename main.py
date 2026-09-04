import os
import logging

from scrapers.scrapers import SSPDownloader
from etl.transform import processar_transformacao
from etl.load import carregar_no_banco

# Configuração do caminho base do projeto
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

# Configuração padrão de logging para o ponto de entrada da aplicação
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def executar_pipeline_completo(ano: int = 2026) -> None:
    """Orquestra e executa o pipeline ETL completo de dados da SSP-SP.

    Este script representa o ponto de entrada (entry point) da aplicação.
    Ele coordena sequencialmente as três etapas fundamentais do pipeline:
        1. Extract: Download do arquivo bruto via web scraping (SSPDownloader).
        2. Transform: Limpeza, normalização e validação dos dados em Pandas.
        3. Load: Carga otimizada e imputação geográfica no banco de dados Django.

    Args:
        ano (int, optional): Ano de referência dos dados de ocorrências
            a serem baixados e processados. Default é 2026.

    Side Effects:
        - Salva o arquivo baixado na pasta `data_raw/`.
        - Gera o arquivo tratado em `data_processed/`.
        - Insere/atualiza registros no banco de dados conectado ao Django.
    Returns:
        None
    """
    logger.info(f"🚀 Iniciando Pipeline ETL para o ano {ano}...")

    # =========================================================================
    # 1. ETAPA 1: SCRAPER / EXTRAÇÃO (SSP-SP)
    # =========================================================================
    downloader = SSPDownloader(pasta_destino="data_raw")
    _, caminho_bruto = downloader.baixar_ano(ano)

    if not caminho_bruto or not os.path.exists(caminho_bruto):
        logger.error(
            f"❌ Pipeline interrompido: Arquivo bruto não foi encontrado em '{caminho_bruto}'."
        )
        return

    # =========================================================================
    # 2. ETAPA 2: TRANSFORMAÇÃO / LIMPEZA (Pandas)
    # =========================================================================
    try:
        df_limpo = processar_transformacao(caminho_bruto, nome_aba=f"CELULAR_{ano}")
    except Exception as e:
        logger.error(f"❌ Falha crítica na etapa de transformação dos dados: {e}")
        return

    # =========================================================================
    # 3. ETAPA 3: CARGA NO BANCO DE DADOS (Django ORM)
    # =========================================================================
    if df_limpo is not None and not df_limpo.empty:
        carregar_no_banco(df_limpo)
        logger.info("🎉 Pipeline ETL concluído com sucesso!")
    else:
        logger.error("❌ Pipeline interrompido: O DataFrame resultante da limpeza está vazio.")


if __name__ == "__main__":
    executar_pipeline_completo(2026)