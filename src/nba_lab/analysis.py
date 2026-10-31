"""Estatísticas puras e detectores univariados; nenhuma dependência da interface."""

import numpy as np
import pandas as pd
from pyod.models.ecod import ECOD
from scipy import stats
from sklearn.cluster import DBSCAN
from sklearn.neighbors import LocalOutlierFactor, NearestNeighbors
from sklearn.preprocessing import StandardScaler

from .schema import VARIABLES

METHODS = ["IQR", "Z-score", "Grubbs", "ECOD", "K-NN", "DBSCAN", "LOF"]


def describe(series: pd.Series) -> dict:
    """Convenções únicas: ddof=1; quartis lineares; todas as modas empatadas."""
    x = series.dropna().astype(float)
    n = len(x)
    q1, median, q3 = x.quantile([0.25, 0.5, 0.75], interpolation="linear")
    mean, sd = x.mean(), x.std(ddof=1)
    skew = float(stats.skew(x, bias=False)) if n >= 3 and x.nunique() > 1 else np.nan
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    modes = x.mode().tolist() if x.value_counts().max() > 1 else []
    central = x[x.between(lower, upper)]
    return {
        "n": n,
        "média": mean,
        "mediana": median,
        "moda": ", ".join(f"{v:.2f}" for v in modes) or "sem repetição",
        "mínimo": x.min(),
        "máximo": x.max(),
        "amplitude": x.max() - x.min(),
        "desvio padrão": sd,
        "variância": x.var(ddof=1),
        "Q1": q1,
        "Q3": q3,
        "IQR": iqr,
        "limite inferior": lower,
        "limite superior": upper,
        "outliers IQR": int((~x.between(lower, upper)).sum()),
        "assimetria": skew,
        "direção": (
            "indefinida"
            if not np.isfinite(skew)
            else "simétrica"
            if abs(skew) < 1e-12
            else "direita"
            if skew > 0
            else "esquerda"
        ),
        "intensidade": (
            "indefinida"
            if not np.isfinite(skew)
            else "aproximadamente simétrica"
            if abs(skew) < 0.5
            else "moderada"
            if abs(skew) < 1
            else "forte"
        ),
        "CV (%)": 100 * sd / mean if mean > 0 else np.nan,
        "IQR/mediana (%)": 100 * iqr / median if median > 0 else np.nan,
        "DP sem extremos IQR": central.std(ddof=1),
    }


def summary(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"time": team, "variável": VARIABLES[col], "campo": col, **describe(group[col])}
            for team, group in frame.groupby("time", sort=True)
            for col in VARIABLES
        ]
    )


def detect(series: pd.Series) -> tuple[pd.DataFrame, dict]:
    """Retorna flags alinhadas ao índice original e parâmetros auditáveis.

    Os detectores são UNIVARIADOS, por time e coluna. Não forçamos uma
    percentagem exata de anomalias em empates: ECOD e kNN usam score > p95.
    Grubbs é bilateral, uma única aplicação, e condicionado a Shapiro p>=0.05.
    """
    x = series.dropna().astype(float)
    flags = pd.DataFrame(False, index=series.index, columns=METHODS)
    meta = {
        "n válido": len(x),
        "Shapiro p": np.nan,
        "G": np.nan,
        "G crítico": np.nan,
        "Grubbs situação": "n<3 ou constante",
        "LOF k efetivo": np.nan,
    }
    if len(x) < 3 or x.nunique() < 2:
        return flags, meta
    d = describe(x)
    flags.loc[x.index, "IQR"] = ~x.between(d["limite inferior"], d["limite superior"])
    flags.loc[x.index, "Z-score"] = ((x - x.mean()) / x.std(ddof=1)).abs() > 3
    n = len(x)
    p = float(stats.shapiro(x).pvalue) if n <= 5000 else np.nan
    g = (x - x.mean()).abs() / x.std(ddof=1)
    t = stats.t.ppf(1 - 0.05 / (2 * n), n - 2)
    critical = (n - 1) / np.sqrt(n) * np.sqrt(t * t / (n - 2 + t * t))
    meta.update(
        {
            "Shapiro p": p,
            "G": g.max(),
            "G crítico": critical,
            "Grubbs situação": "aplicado"
            if p >= 0.05
            else "não aplicado: normalidade não sustentada",
        }
    )
    if p >= 0.05 and g.max() > critical:
        flags.loc[g.idxmax(), "Grubbs"] = True
    z = StandardScaler().fit_transform(x.to_numpy().reshape(-1, 1))
    k = min(5, n - 1)
    distances = NearestNeighbors(n_neighbors=k + 1).fit(z).kneighbors(z)[0][:, -1]
    flags.loc[x.index, "K-NN"] = distances > np.quantile(distances, 0.95)
    ecod = ECOD(contamination=0.05, n_jobs=1).fit(z)
    flags.loc[x.index, "ECOD"] = ecod.decision_scores_ > ecod.threshold_
    flags.loc[x.index, "DBSCAN"] = DBSCAN(eps=0.5, min_samples=5).fit_predict(z) == -1
    # Incluir pelo menos um vizinho de valor diferente evita densidades quase
    # infinitas em contagens com muitos empates. Nunca excluir jogos repetidos.
    lof_k = min(max(20, int(x.value_counts().max())), n - 1)
    flags.loc[x.index, "LOF"] = (
        LocalOutlierFactor(n_neighbors=lof_k, contamination=0.05).fit_predict(z) == -1
    )
    meta["LOF k efetivo"] = lof_k
    return flags, meta


def audit_outliers(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Contagem por coluna numérica e time; detalhes para rastrear os jogos."""
    counts, records = [], []
    excluded = {"venceu"}  # binária não possui caudas quantitativas interpretáveis
    columns = [c for c in frame.select_dtypes(include="number").columns if c not in excluded]
    for team, group in frame.groupby("time"):
        for col in columns:
            flags, meta = detect(group[col])
            counts.append({"time": team, "campo": col, **flags.sum().astype(int).to_dict(), **meta})
            for method in METHODS:
                for idx in flags.index[flags[method]]:
                    records.append(
                        {
                            "linha Excel": int(idx) + 2,
                            "time": team,
                            "jogo": group.at[idx, "jogo_id"],
                            "data": group.at[idx, "data_jogo"],
                            "campo": col,
                            "valor": group.at[idx, col],
                            "método": method,
                        }
                    )
    return pd.DataFrame(counts), pd.DataFrame(
        records, columns=["linha Excel", "time", "jogo", "data", "campo", "valor", "método"]
    )


def interpretations(table: pd.DataFrame, variable: str) -> list[str]:
    """Texto gerado dos resultados reais, sem transformar associação em causalidade."""
    rows = table[table.campo == variable]
    messages = []
    for _, r in rows.iterrows():
        if r["n"] == 0:
            messages.append(f"{r.time}: não há observações válidas.")
            continue
        caution = (
            " A média abaixo de 5 exige cautela com a inflação do CV." if r["média"] < 5 else ""
        )
        robust = (
            (
                "A mediana e IQR são preferíveis para descrever o centro e a dispersão; "
                "avaliar log1p apenas em análises futuras, preservando a interpretação."
            )
            if r["intensidade"] == "forte"
            else (
                "Média e mediana devem ser lidas em conjunto; não há indicação de "
                "transformação apenas por esse coeficiente."
            )
        )
        messages.append(
            f"{r.time}: {int(r['n'])} jogos; média {r['média']:.2f}, mediana {r['mediana']:.2f}. "
            f"Assimetria {r['assimetria']:.2f} ({r['direção']}, {r['intensidade']}). {robust} "
            f"CV {r['CV (%)']:.2f}%: o desvio equivale a essa proporção da média.{caution} "
            f"Os 50% centrais ficam entre {r['Q1']:.2f} e {r['Q3']:.2f}, faixa de "
            f"{r['IQR']:.2f}; a amplitude total é {r['amplitude']:.2f}. "
            f"Há {int(r['outliers IQR'])} extremos IQR; o DP passa de "
            f"{r['desvio padrão']:.2f} a {r['DP sem extremos IQR']:.2f} ao excluí-los apenas "
            "nesta análise de sensibilidade. Essa diferença não prova erro de registro."
        )
        bowley = (r["Q3"] + r["Q1"] - 2 * r["mediana"]) / r["IQR"] if r["IQR"] else 0
        agreement = "concorda" if bowley * r["assimetria"] > 0 else "diverge ou é neutra"
        messages.append(
            f"{r.time}: a posição da mediana na caixa (Bowley {bowley:.2f}) {agreement} "
            "em direção com Fisher–Pearson. O boxplot resume a metade central, enquanto "
            "Fisher–Pearson dá grande peso às caudas; por isso podem divergir. No histograma, "
            "a KDE suaviza os valores inteiros e sua forma também depende da largura de banda."
        )
    if len(rows) > 1:
        for metric, explanation in [("CV (%)", "dispersão relativa"), ("IQR", "dispersão central")]:
            valid = rows.dropna(subset=[metric])
            if len(valid):
                low, high = valid[metric].min(), valid[metric].max()
                least = ", ".join(valid.loc[valid[metric].eq(low), "time"])
                most = ", ".join(valid.loc[valid[metric].eq(high), "time"])
                messages.append(
                    f"Em {VARIABLES[variable]}, menor {explanation}: {least} "
                    f"({low:.2f}); maior: {most} ({high:.2f}). Empates são preservados."
                )
    return messages
