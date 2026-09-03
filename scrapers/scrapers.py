import hashlib
import os
import time
import httpx


class SSPDownloader:
    """
    Gerencia o download e a validação das bases públicas de dados da SSP-SP.

    Atributos:
        pasta_destino (str): Caminho absoluto da pasta onde os arquivos serão salvos.
    """

    def __init__(self, pasta_destino: str = "data_raw"):
        """
        Inicializa o downloader garantindo a existência da pasta de destino.

        Args:
            pasta_destino (str, optional): Nome/caminho relativo da pasta para armazenar
                                           os downloads. Padrão: "data_raw".
        """
        raiz_projeto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.pasta_destino = os.path.join(raiz_projeto, pasta_destino)
        os.makedirs(self.pasta_destino, exist_ok=True)

    def _gerar_hash(self, caminho_arquivo: str) -> str:
        """
        Gera o checksum MD5 de um arquivo lido em blocos para evitar alto consumo de RAM.

        Args:
            caminho_arquivo (str): Caminho completo do arquivo a ser lido.

        Returns:
            str: Hash MD5 em formato hexadecimal.
        """
        hasher = hashlib.md5()
        with open(caminho_arquivo, "rb") as f:
            for bloco in iter(lambda: f.read(65536), b""):
                hasher.update(bloco)
        return hasher.hexdigest()

    def baixar_ano(self, ano: int, max_tentativas: int = 3) -> tuple[bool, str]:
        """
        Realiza o download da base de dados de um determinado ano, monitorando o progresso,
        efetuando retentativas automáticas e validando alteração no arquivo via hash MD5.

        Args:
            ano (int): Ano da base de dados a ser baixada (ex: 2026).
            max_tentativas (int, optional): Número máximo de tentativas de download em caso
                                            de instabilidade de rede. Padrão: 3.

        Returns:
            tuple[bool, str]:
                - bool: True se o arquivo foi baixado/atualizado e precisa ser processado no banco.
                        False se o arquivo já existia e não teve alterações (ou se houve falha).
                - str: Caminho absoluto do arquivo oficial (ou None caso falhe e não exista localmente).
        """
        link_ssp = f"https://www.ssp.sp.gov.br/assets/estatistica/transparencia/baseDados/celularesSub/CelularesSubtraidos_{ano}.xlsx"

        caminho_oficial = os.path.join(self.pasta_destino, f"CelularesSubtraidos_{ano}.xlsx")
        caminho_temp = os.path.join(self.pasta_destino, f"CelularesSubtraidos_{ano}_temp.xlsx")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        timeout_config = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=30.0)

        for tentativa in range(1, max_tentativas + 1):
            print(f"\n🔍 [1/4 Extração] Conectando ao servidor da SSP-SP (Ano {ano}) - Tentativa {tentativa}/{max_tentativas}...")

            try:
                with httpx.Client(timeout=timeout_config, follow_redirects=True) as client:
                    with client.stream("GET", link_ssp, headers=headers) as resposta:
                        if resposta.status_code != 200:
                            print(f"❌ Erro HTTP {resposta.status_code}: Não foi possível acessar a base de {ano}.")
                            caminho_retorno = caminho_oficial if os.path.exists(caminho_oficial) else None
                            return False, caminho_retorno

                        tamanho_total = int(resposta.headers.get("content-length", 0))
                        chunk_size = 128 * 1024  # 128 KB por pacote

                        if tamanho_total > 0:
                            total_pacotes = (tamanho_total // chunk_size) + 1
                            print(f"📊 Tamanho: {tamanho_total / (1024 * 1024):.2f} MB (~{total_pacotes} pacotes)")

                        tamanho_baixado = 0
                        numero_pacote = 0

                        with open(caminho_temp, "wb") as arquivo_temp:
                            for pedaco in resposta.iter_bytes(chunk_size=chunk_size):
                                if pedaco:
                                    arquivo_temp.write(pedaco)
                                    tamanho_baixado += len(pedaco)
                                    numero_pacote += 1

                                    if tamanho_total > 0:
                                        pct = (tamanho_baixado / tamanho_total) * 100
                                        print(
                                            f"   Pacote #{numero_pacote:04d} | {pct:.1f}% concluído | Baixado: {tamanho_baixado / (1024 * 1024):.2f} MB",
                                            end="\r",
                                        )

                print(f"\n🔬 Verificando integridade (MD5) do arquivo de {ano}...")

                # Primeira execução: se não existe arquivo oficial local
                if not os.path.exists(caminho_oficial):
                    os.rename(caminho_temp, caminho_oficial)
                    print(f"✅ Arquivo baixado com sucesso: CelularesSubtraidos_{ano}.xlsx")
                    return True, caminho_oficial

                # Comparação de MD5 para arquivos existentes
                hash_local = self._gerar_hash(caminho_oficial)
                hash_temp = self._gerar_hash(caminho_temp)

                if hash_local != hash_temp:
                    os.replace(caminho_temp, caminho_oficial)
                    print(f"🔄 A base do ano {ano} mudou no portal! Arquivo atualizado.")
                    return True, caminho_oficial
                else:
                    if os.path.exists(caminho_temp):
                        os.remove(caminho_temp)
                    print(f"ℹ️ O arquivo local do ano {ano} já está atualizado. Nenhuma alteração.")
                    return False, caminho_oficial

            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.NetworkError) as e:
                print(f"\n⚠️ Instabilidade de rede/timeout na tentativa {tentativa}: {e}")
                if os.path.exists(caminho_temp):
                    os.remove(caminho_temp)

                if tentativa < max_tentativas:
                    tempo_espera = tentativa * 5
                    print(f"⏳ Aguardando {tempo_espera}s para tentar novamente...")
                    time.sleep(tempo_espera)
                else:
                    print(f"\n❌ Falha definitiva no download do ano {ano} após {max_tentativas} tentativas.")
                    caminho_retorno = caminho_oficial if os.path.exists(caminho_oficial) else None
                    return False, caminho_retorno

            except Exception as e:
                print(f"\n❌ Erro inesperado no download do ano {ano}: {e}")
                if os.path.exists(caminho_temp):
                    os.remove(caminho_temp)
                caminho_retorno = caminho_oficial if os.path.exists(caminho_oficial) else None
                return False, caminho_retorno

        caminho_retorno = caminho_oficial if os.path.exists(caminho_oficial) else None
        return False, caminho_retorno