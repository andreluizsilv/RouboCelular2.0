import os
import django
import pandas as pd
from django.db import transaction
from tqdm import tqdm

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from ocorrencias.models import Endereco, OcorrenciaCelular
from etl.enrichment import preencher_coordenadas_por_media_bairro


def normalizar_texto(val) -> str:
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip().upper()
    return "" if s in ["NAN", "NONE", "NULL", "<NA>"] else s


def carregar_enderecos(df: pd.DataFrame, tamanho_lote: int = 5000) -> dict:
    col_logr = "LOGRADOURO" if "LOGRADOURO" in df.columns else "DESCR_LOGRADOURO"
    col_bair = "BAIRRO" if "BAIRRO" in df.columns else "DESCR_BAIRRO"
    col_cida = "CIDADE" if "CIDADE" in df.columns else "DESCR_CIDADE"

    df_enderecos = df.dropna(subset=[col_logr]).drop_duplicates(
        subset=[col_logr, col_bair, col_cida]
    )

    enderecos_existentes = set(
        Endereco.objects.values_list("logradouro", "bairro", "cidade")
    )
    enderecos_existentes = {
        (normalizar_texto(logr), normalizar_texto(bair), normalizar_texto(cid))
        for logr, bair, cid in enderecos_existentes
    }

    novos_enderecos = []

    for _, row in tqdm(
        df_enderecos.iterrows(),
        total=len(df_enderecos),
        desc="📍 Processando Endereços",
        unit="end",
    ):
        logr = normalizar_texto(row.get(col_logr))
        bair = normalizar_texto(row.get(col_bair))
        cid = normalizar_texto(row.get(col_cida))

        if not logr:
            continue

        chave = (logr, bair, cid)

        if chave not in enderecos_existentes:
            lat_val = row.get("LATITUDE")
            long_val = row.get("LONGITUDE")

            def converter_float(val):
                if pd.isna(val) or val is None:
                    return None
                try:
                    return float(str(val).replace(",", ".").strip())
                except ValueError:
                    return None

            novos_enderecos.append(
                Endereco(
                    logradouro=logr,
                    bairro=bair,
                    cidade=cid,
                    latitude=converter_float(lat_val),
                    longitude=converter_float(long_val),
                )
            )
            enderecos_existentes.add(chave)

    if novos_enderecos:
        Endereco.objects.bulk_create(
            novos_enderecos, batch_size=tamanho_lote, ignore_conflicts=True
        )

    return {
        (normalizar_texto(e.logradouro), normalizar_texto(e.bairro), normalizar_texto(e.cidade)): e
        for e in Endereco.objects.all()
    }


def carregar_ocorrencias(df: pd.DataFrame, mapa_enderecos: dict, tamanho_lote: int = 5000):
    def buscar_coluna(opcoes):
        for col in opcoes:
            if col in df.columns:
                return col
        return None

    col_num_bo = buscar_coluna(["NUM_BO", "NUMERO_BOLETIM", "BO_NUMERO", "NUMERO_BO"])
    col_delegacia = buscar_coluna(["DELEGACIA_NOME", "NOME_DELEGACIA", "DELEGACIA", "DP"])
    col_logr = buscar_coluna(["LOGRADOURO", "DESCR_LOGRADOURO"]) or "LOGRADOURO"
    col_bair = buscar_coluna(["BAIRRO", "DESCR_BAIRRO"]) or "BAIRRO"
    col_cida = buscar_coluna(["CIDADE", "DESCR_CIDADE"]) or "CIDADE"

    bos_existentes = set(
        OcorrenciaCelular.objects.values_list("num_bo", "delegacia_nome")
    )
    bos_existentes = {
        (str(num), normalizar_texto(del_nome))
        for num, del_nome in bos_existentes
    }

    novas_ocorrencias = []

    for _, row in tqdm(
        df.iterrows(),
        total=len(df),
        desc="📱 Processando Ocorrências",
        unit="reg",
    ):
        val_num = row.get(col_num_bo) if col_num_bo else None
        val_del = row.get(col_delegacia) if col_delegacia else "DELEGACIA NAO INFORMADA"

        if pd.isna(val_num) or str(val_num).strip() in ["", "nan", "None", "<NA>"]:
            continue

        try:
            num_bo_str = "".join(filter(str.isdigit, str(val_num).split(".")[0]))
            if not num_bo_str:
                continue
            num_bo = str(num_bo_str)

            delegacia = (
                normalizar_texto(val_del)
                if pd.notna(val_del)
                else "DELEGACIA NAO INFORMADA"
            )
        except (ValueError, TypeError):
            continue

        chave_bo = (num_bo, delegacia)
        if chave_bo in bos_existentes:
            continue

        logr = normalizar_texto(row.get(col_logr))
        bair = normalizar_texto(row.get(col_bair))
        cid = normalizar_texto(row.get(col_cida))

        endereco_obj = mapa_enderecos.get((logr, bair, cid))

        novas_ocorrencias.append(
            OcorrenciaCelular(
                num_bo=num_bo,
                delegacia_nome=delegacia,
                data_ocorrencia=row.get("DATA_OCORRENCIA")
                if pd.notna(row.get("DATA_OCORRENCIA"))
                else None,
                hora_ocorrencia=row.get("HORA_OCORRENCIA")
                if pd.notna(row.get("HORA_OCORRENCIA"))
                else None,
                marca_celular=str(row.get("MARCA_CELULAR")).strip()
                if pd.notna(row.get("MARCA_CELULAR"))
                else None,
                endereco=endereco_obj,
            )
        )
        bos_existentes.add(chave_bo)

        if len(novas_ocorrencias) >= tamanho_lote:
            OcorrenciaCelular.objects.bulk_create(
                novas_ocorrencias, batch_size=tamanho_lote, ignore_conflicts=True
            )
            novas_ocorrencias = []

    if novas_ocorrencias:
        OcorrenciaCelular.objects.bulk_create(
            novas_ocorrencias, batch_size=tamanho_lote, ignore_conflicts=True
        )


def carregar_no_banco(df: pd.DataFrame, tamanho_lote: int = 5000):
    if df is None or df.empty:
        return

    with transaction.atomic():
        mapa_enderecos = carregar_enderecos(df, tamanho_lote=tamanho_lote)
        preencher_coordenadas_por_media_bairro()
        carregar_ocorrencias(df, mapa_enderecos=mapa_enderecos, tamanho_lote=tamanho_lote)