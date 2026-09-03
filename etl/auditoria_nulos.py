import os
import pandas as pd

# Caminho para o arquivo limpo
RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_EXCEL_LIMPO = os.path.join(RAIZ_PROJETO, "data_processed", "celulares_limpos.xlsx")


def auditar_nulos():
    print(f"⏳ Lendo arquivo limpo em: {CAMINHO_EXCEL_LIMPO}...")

    if not os.path.exists(CAMINHO_EXCEL_LIMPO):
        print("❌ Arquivo não encontrado! Execute 'python etl/transform.py' primeiro para gerar a planilha.")
        return

    df = pd.read_excel(CAMINHO_EXCEL_LIMPO)
    total_linhas = len(df)

    print("\n" + "=" * 50)
    print(f"📊 RELATÓRIO DE AUDITORIA DE DADOS NULOS")
    print(f"Total de registros na base: {total_linhas:,} linhas")
    print("=" * 50)

    # Contagem de nulos
    nulos_por_coluna = df.isnull().sum()
    porcentagem_nulos = (nulos_por_coluna / total_linhas) * 100

    relatorio = pd.DataFrame({
        'Total Nulos': nulos_por_coluna,
        'Porcentagem (%)': porcentagem_nulos.round(2)
    })

    # Ordena mostrando primeiro quem tem nulos
    relatorio_ordenado = relatorio.sort_values(by='Total Nulos', ascending=False)

    print("\n📋 Detalhamento por Coluna:")
    print(relatorio_ordenado.to_string())

    print("\n" + "-" * 50)
    print("📍 ESTATÍSTICAS DE GEOCODIFICAÇÃO / ENDEREÇOS:")
    print(
        f"  • Registros Sem Coordenadas (LAT/LONG nulas): {df['LATITUDE'].isna().sum():,} ({df['LATITUDE'].isna().mean() * 100:.2f}%)")
    print(f"  • CEPs válidos preenchidos: {df['CEP'].notna().sum():,} ({df['CEP'].notna().mean() * 100:.2f}%)")

    # Endereços únicos que podem ir para a tabela EnderecoReferencia
    enderecos_unicos = df[['LOGRADOURO', 'BAIRRO', 'CIDADE']].drop_duplicates().shape[0]
    print(f"  • Total de Combinações Únicas de Endereço (Rua + Bairro + Cidade): {enderecos_unicos:,}")
    print("=" * 50)


if __name__ == "__main__":
    auditar_nulos()