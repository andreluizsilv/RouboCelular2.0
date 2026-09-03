import os
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def salvar_em_parquet(df: pd.DataFrame, nome_arquivo: str = "celulares_limpos.parquet") -> str:
    """
    Salva o DataFrame limpo no formato Parquet compactado (snappy).
    """
    raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta_processada = os.path.join(raiz_projeto, "data_processed")
    os.makedirs(pasta_processada, exist_ok=True)

    caminho_saida = os.path.join(pasta_processada, nome_arquivo)

    # Salva com compressão Snappy otimizada para leitura rápida
    df.to_parquet(caminho_saida, index=False, compression="snappy")

    tamanho_mb = os.path.getsize(caminho_saida) / (1024 * 1024)
    logging.info(f"💾 Base tratada salva com sucesso em Parquet: {caminho_saida} ({tamanho_mb:.2f} MB)")

    return caminho_saida