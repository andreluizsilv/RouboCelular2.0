import os
import logging
from scrapers.scrapers import SSPDownloader
from etl.transform import processar_transformacao
from etl.load import carregar_no_banco

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def executar_pipeline_completo(ano: int = 2026):
    logging.info(f"🚀 Iniciando Pipeline ETL para o ano {ano}...")

    # 1. ETAPA 1: SCRAPER / EXTRAÇÃO (SSP-SP)
    downloader = SSPDownloader(pasta_destino="data_raw")
    _, caminho_bruto = downloader.baixar_ano(ano)

    if not os.path.exists(caminho_bruto):
        logging.error(f"❌ Pipeline interrompido: Arquivo bruto não foi encontrado em {caminho_bruto}.")
        return

    # 2. ETAPA 2: TRANSFORMAÇÃO / LIMPEZA
    try:
        df_limpo = processar_transformacao(caminho_bruto, nome_aba=f"CELULAR_{ano}")
    except Exception as e:
        logging.error(f"❌ Falha na transformação dos dados: {e}")
        return

    # 3. ETAPA 3: CARGA NO BANCO DE DADOS (DJANGO)
    if df_limpo is not None and not df_limpo.empty:
        carregar_no_banco(df_limpo)
        logging.info("🎉 Pipeline concluído com sucesso!")
    else:
        logging.error("❌ Pipeline interrompido: DataFrame limpo está vazio.")

if __name__ == "__main__":
    executar_pipeline_completo(2026)