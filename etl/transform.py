import os
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def limpar_texto(coluna: pd.Series) -> pd.Series:
    return coluna.astype(str).str.strip().str.upper().replace({"NAN": np.nan, "NONE": np.nan, "": np.nan})


def processar_transformacao(caminho_excel: str, nome_aba: str = "CELULAR_2026") -> pd.DataFrame:
    logging.info(f"📖 Lendo aba '{nome_aba}' do arquivo Excel: {caminho_excel}...")
    df = pd.read_excel(caminho_excel, sheet_name=nome_aba)

    logging.info(f"📊 Total de linhas brutas lidas: {len(df)}")

    # 1. Padronização dos cabeçalhos
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(" ", "_")
        .str.replace("º", "")
        .str.replace("ª", "")
    )

    # Remove nomes de colunas duplicados
    df = df.loc[:, ~df.columns.duplicated()].copy()

    # 2. Mapeamento de sinonímias
    colunas_renomear = {
        "NUMERO_BOLETIM": "NUM_BO",
        "NUMERO_BOLETIM_OCORRENCIA": "NUM_BO",
        "NUM_BOLETIM": "NUM_BO",
        "ANO_BOLETIM": "ANO_BO",
        "DATA_OCORRENCIA_BO": "DATA_OCORRENCIA",
        "DATA_OCORRENCIA_BOLETIM": "DATA_OCORRENCIA",
        "HORA_OCORRENCIA_BOLETIM": "HORA_OCORRENCIA",
        "NOME_DELEGACIA": "DELEGACIA_NOME",
        "NOME_MUNICIPIO": "CIDADE",
        "DESCRICAO_APARELHO": "MARCA_CELULAR",
        "MARCA_APARELHO": "MARCA_CELULAR",
        "DESCR_MARCA_CELULAR": "MARCA_CELULAR",
        "MARCA_OBJETO": "MARCA_CELULAR"
    }

    df.rename(columns=colunas_renomear, inplace=True)
    df = df.loc[:, ~df.columns.duplicated()].copy()

    # 3. Filtro de linhas institucionais e nulas
    coluna_ref = "NUM_BO" if "NUM_BO" in df.columns else df.columns[0]
    df = df[df[coluna_ref].notna()].copy()
    df = df[~df[coluna_ref].astype(str).str.contains("METODOLOGIA|INTERPRETAÇÃO|FONTE:", case=False, na=False)].copy()

    # 4. SELEÇÃO AMPLIADA DE COLUNAS (Incluindo Rubrica, Conduta, Local e Período)
    colunas_finais_desejadas = [
        "NUM_BO", "ANO_BO", "DATA_OCORRENCIA", "HORA_OCORRENCIA", "DESCR_PERIODO",
        "RUBRICA", "DESCR_CONDUTA", "DESCR_TIPOLOCAL", "MARCA_CELULAR",
        "LOGRADOURO", "BAIRRO", "CIDADE", "UF", "CEP", "DELEGACIA_NOME",
        "LATITUDE", "LONGITUDE"
    ]

    colunas_existentes = [c for c in colunas_finais_desejadas if c in df.columns]
    df = df[colunas_existentes].copy()

    # 5. Limpeza de campos de texto
    colunas_texto = [
        "RUBRICA", "DESCR_CONDUTA", "DESCR_TIPOLOCAL", "DESCR_PERIODO",
        "LOGRADOURO", "BAIRRO", "CIDADE", "UF", "DELEGACIA_NOME", "MARCA_CELULAR", "CEP"
    ]
    for col in colunas_texto:
        if col in df.columns:
            df[col] = limpar_texto(df[col].squeeze())

    # 6. Normalização de Latitude e Longitude
    for col in ["LATITUDE", "LONGITUDE"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce")

    # 7. Normalização de Data
    if "DATA_OCORRENCIA" in df.columns:
        df["DATA_OCORRENCIA"] = pd.to_datetime(df["DATA_OCORRENCIA"], errors="coerce").dt.strftime('%Y-%m-%d')

    logging.info(f"✅ Total de registros válidos processados: {len(df)}")
    logging.info(f"📋 Colunas mantidas: {list(df.columns)}")

    # 8. Persistência
    raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta_processada = os.path.join(raiz_projeto, "data_processed")
    os.makedirs(pasta_processada, exist_ok=True)

    caminho_saida = os.path.join(pasta_processada, "celulares_limpos.xlsx")
    df.to_excel(caminho_saida, index=False)
    logging.info(f"💾 Base tratada salva em: {caminho_saida}")

    return df