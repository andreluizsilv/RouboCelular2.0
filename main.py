import os
import sys
import logging

# Adiciona o diretório raiz ao path
RAIZ_PROJETO = os.path.dirname(os.path.abspath(__file__))
sys.path.append(RAIZ_PROJETO)

from scrapers.scrapers import SSPDownloader
from etl.transform import processar_transformacao


def rodar_pipeline_ano(ano: int, forcar_reprocessamento: bool = False):
    print(f"\n==================================================")
    print(f"🚀 INICIANDO PIPELINE ETL DE ROUBO DE CELULARES: {ano}")
    print(f"==================================================")

    # 1. EXTRAÇÃO (Download + MD5 Check)
    downloader = SSPDownloader(pasta_destino="data_raw")
    arquivo_atualizado, caminho_excel = downloader.baixar_ano(ano)

    # VALIDAÇÃO CRÍTICA: Garante que o arquivo físico realmente existe antes de avançar
    if not os.path.exists(caminho_excel):
        print(f"\n❌ [ABORTADO] O arquivo '{caminho_excel}' não existe na pasta raw. O download falhou ou o link está indisponível.")
        return

    # Se o arquivo não mudou e o usuário não forçou, encerra o ciclo
    if not arquivo_atualizado and not forcar_reprocessamento:
        print(f"⏭️ [200 OK] O banco de dados para {ano} já está em dia. Pulando etapas seguintes.")
        return

    # 2. TRANSFORMAÇÃO (Só roda se o arquivo realmente existir)
    print(f"\n🧹 [2/4 Transformação] Limpando e padronizando a base de {ano}...")
    df_limpo = processar_transformacao(caminho_excel)
    print(f"📊 [2/4 Concluído] Registros prontos para enriquecimento: {len(df_limpo):,}")

    # 3. ENRIQUECIMENTO (Aguardando implementação)
    print(f"\n🗺️ [3/4 Geolocalização] Consultando cache / buscando coordenadas...")

    # 4. CARGA (Aguardando implementação)
    print(f"\n💾 [4/4 Carga] Inserindo/Atualizando registros no PostgreSQL...")

    print(f"\n✅ PIPELINE FINALIZADO COM SUCESSO PARA O ANO {ano}!")


if __name__ == "__main__":
    ANOS = [2026]

    for ano in ANOS:
        rodar_pipeline_ano(ano=ano, forcar_reprocessamento=True)