import os
import pandas as pd
import numpy as np
import pytest
from etl.transform import processar_transformacao


@pytest.fixture
def criar_excel_ssp_mock(tmp_path):
    """Cria um arquivo Excel temporário simulando a estrutura bruta da SSP-SP."""
    caminho_arquivo = tmp_path / "mock_ssp.xlsx"

    # Dados simulados com colunas duplicadas, notas de rodapé e diferentes marcas/rubricas
    dados = {
        "NUM_BOLETIM": ["100/2026", "101/2026", "FONTE: METODOLOGIA SSP", np.nan],
        "ANO_BOLETIM": [2026, 2026, np.nan, np.nan],
        "DATA_OCORRENCIA_BO": ["2026-01-15", "2026-01-16", np.nan, np.nan],
        "RUBRICA": ["Roubo (art. 157)", "Furto (art. 155)", np.nan, np.nan],
        "DESCRICAO_APARELHO": ["  Apple  ", "Samsung", np.nan, np.nan],
        "LATITUDE": ["-23,5505", "-23.5510", np.nan, np.nan],
        "LONGITUDE": ["-46,6333", "-46.6340", np.nan, np.nan],
    }

    df_mock = pd.DataFrame(dados)

    # Salva na aba 'CELULAR_2026'
    with pd.ExcelWriter(caminho_arquivo, engine="openpyxl") as writer:
        df_mock.to_excel(writer, sheet_name="CELULAR_2026", index=False)

    return str(caminho_arquivo)


def test_processar_transformacao_sucesso(criar_excel_ssp_mock):
    caminho_mock = criar_excel_ssp_mock
    df_resultado = processar_transformacao(caminho_mock, nome_aba="CELULAR_2026")

    # Validações
    assert len(df_resultado) == 2  # Deve descartar a linha de rodapé e a linha nula
    assert "MARCA_CELULAR" in df_resultado.columns
    assert "NUM_BO" in df_resultado.columns
    assert df_resultado["MARCA_CELULAR"].iloc[0] == "APPLE"
    assert df_resultado["LATITUDE"].iloc[0] == -23.5505  # Converteu vírgula para float