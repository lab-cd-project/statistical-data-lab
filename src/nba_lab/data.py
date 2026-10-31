"""Leitura sem sobrescrever a fonte, limpeza rastreável e auditoria por coluna."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .schema import RATIOS, SCHEMA


@dataclass
class Dataset:
    raw: pd.DataFrame
    clean: pd.DataFrame
    quality: pd.DataFrame
    changes: pd.DataFrame
    duplicates: int
    duplicate_keys: int
    path: Path


def load_dataset(path: Path, teams: tuple[str, ...] | None = None) -> Dataset:
    """Converte tipos e reconstrói taxas das contagens, preservando índices da fonte.

    Percentuais de origem misturam 0.506 e 506. Não dividimos todos por mil:
    recalculamos com os numeradores/denominadores, inclusive valores em [0,1].
    Duplicatas não são apagadas silenciosamente. Valores inválidos viram NA.
    """
    raw = pd.read_excel(path, engine="openpyxl")
    if set(raw.columns) != set(SCHEMA):
        raise ValueError("Colunas da planilha diferem do contrato em schema.py.")
    if teams is not None:
        # Filtrar antes da auditoria mantém todo o relatório no mesmo escopo.
        # Não reiniciar índices: eles identificam as linhas na planilha original.
        raw = raw.loc[raw["TEAM_NAME"].isin(teams)].copy()
    clean = raw.rename(columns={k: v.name for k, v in SCHEMA.items()}).copy()
    invalid = pd.DataFrame(False, index=clean.index, columns=clean.columns)
    changes = []
    for original, spec in SCHEMA.items():
        s = raw[original]
        if spec.kind == "data":
            if pd.api.types.is_datetime64_any_dtype(s):
                converted = pd.to_datetime(s, errors="coerce")
            elif pd.api.types.is_numeric_dtype(s):
                converted = pd.to_datetime(s, unit="D", origin="1899-12-30", errors="coerce")
            else:
                # Strings ISO aceitas; formatos ambíguos não são adivinhados.
                converted = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
            invalid[spec.name] = s.notna() & converted.isna()
            clean[spec.name] = converted
        elif spec.kind in ("texto", "categórica nominal"):
            clean[spec.name] = s.astype("string").str.strip().replace("", pd.NA)
        else:
            source = s.replace({"W": 1, "L": 0}) if spec.name == "venceu" else s
            converted = pd.to_numeric(source, errors="coerce")
            bad = s.notna() & (converted.isna() | ~np.isfinite(converted))
            bad |= converted.lt(0)
            if spec.kind in ("identificador", "numérica discreta", "binária"):
                bad |= converted.notna() & converted.mod(1).ne(0)
            if spec.kind == "binária":
                bad |= converted.notna() & ~converted.isin([0, 1])
            if spec.name in RATIOS:
                bad |= converted.gt(1)
            invalid[spec.name] = bad
            clean[spec.name] = converted.mask(bad)
            if spec.kind == "identificador":
                clean[spec.name] = clean[spec.name].astype("Int64").astype("string")

    # Checagens cruzadas: apenas sinalizam; uma divergência não informa qual lado errou.
    for made, attempted in [
        ("arremessos_convertidos", "arremessos_tentados"),
        ("cestas_tres", "tentativas_tres"),
        ("lances_livres_convertidos", "lances_livres_tentados"),
    ]:
        mask = clean[made].gt(clean[attempted])
        invalid.loc[mask, [made, attempted]] = True
    identities = {
        "rebotes": clean.rebotes_ofensivos + clean.rebotes_defensivos,
        "pontos": 2 * clean.arremessos_convertidos
        + clean.cestas_tres
        + clean.lances_livres_convertidos,
    }
    for col, expected in identities.items():
        invalid[col] |= clean[col].notna() & expected.notna() & clean[col].ne(expected)

    for ratio, (numerator, denominator) in RATIOS.items():
        den = (
            clean[denominator]
            if denominator
            else (clean.vitorias_acumuladas + clean.derrotas_acumuladas)
        )
        computed = clean[numerator] / den.replace(0, np.nan)
        original = pd.to_numeric(
            raw[next(k for k, v in SCHEMA.items() if v.name == ratio)], errors="coerce"
        )
        changed = ~np.isclose(original, computed, atol=0.00051, rtol=0, equal_nan=True)
        invalid[ratio] |= changed & original.notna()
        clean[ratio] = computed
        changes.append(
            {
                "campo": ratio,
                "células recalculadas": int(changed.sum()),
                "regra": "numerador / denominador; denominador zero → ausente",
            }
        )

    rows = []
    for original, spec in SCHEMA.items():
        numeric = pd.to_numeric(raw[original], errors="coerce")
        rows.append(
            {
                "original": original,
                "campo": spec.name,
                "tipo original": str(raw[original].dtype),
                "tipo tratado": spec.kind,
                "ausentes origem": int(raw[original].isna().sum()),
                "ausentes tratados": int(clean[spec.name].isna().sum()),
                "zeros origem": int(numeric.eq(0).sum()),
                "negativos origem": int(numeric.lt(0).sum()),
                "inconsistentes": int(invalid[spec.name].sum()),
            }
        )
    return Dataset(
        raw,
        clean,
        pd.DataFrame(rows),
        pd.DataFrame(changes),
        int(raw.duplicated().sum()),
        int(clean.duplicated(["time_id", "jogo_id"]).sum()),
        path,
    )


def model_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Exemplo conservador: prever pontos ANTES do jogo, sem vazamento temporal.

    Nenhuma estatística da partida atual ou saldo que já a inclua pode entrar.
    Etapas futuras devem construir lags por time e validar por corte temporal.
    """
    result = pd.DataFrame(index=frame.index)
    result["em_casa"] = frame.confronto.str.contains("vs.", regex=False).astype("Int64")
    result["dia_semana"] = frame.data_jogo.dt.dayofweek.astype("Int64")
    result["mes"] = frame.data_jogo.dt.month.astype("Int64")
    return result
