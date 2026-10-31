"""Orquestração HTTP do Projeto 1. Cálculos ficam nos serviços independentes."""

from functools import lru_cache
from pathlib import Path

import pandas as pd
from flask import Blueprint, Response, abort, current_app, redirect, render_template, request
from markupsafe import Markup
from plotly.offline import get_plotlyjs

from .analysis import audit_outliers, interpretations, summary
from .charts import boxplot, comparison, histogram
from .data import load_dataset, model_features
from .schema import SCHEMA, VARIABLES

bp = Blueprint("project1", __name__)
METRICS = ["média", "mediana", "desvio padrão", "CV (%)", "IQR", "z médio"]
GROUP_TEAMS = ("Los Angeles Clippers", "Miami Heat")


@lru_cache(maxsize=2)
def _dataset(path: str, modified: int):
    return load_dataset(Path(path), teams=GROUP_TEAMS)


@lru_cache(maxsize=8)
def _analysis(path: str, modified: int, teams: tuple[str, ...]):
    data = _dataset(path, modified)
    frame = data.clean[data.clean.time.isin(teams)].copy()
    counts, records = audit_outliers(frame)
    return frame, summary(frame), counts, records


def table(frame: pd.DataFrame) -> Markup:
    """Escapa conteúdo da fonte e padroniza números; unidade fica no cabeçalho/contexto."""
    frame = frame.rename_axis(None, axis=1)
    return Markup(
        frame.to_html(
            index=False,
            border=0,
            classes="data-table",
            float_format=lambda x: f"{x:.2f}",
            na_rep="N/A",
            escape=True,
        )
    )


def selection():
    path = Path(current_app.config["DATA_PATH"]).resolve()
    if not path.is_file():
        abort(503, description="Base não encontrada. Configure NBA_DATA_PATH e reinicie.")
    modified = path.stat().st_mtime_ns
    data = _dataset(str(path), modified)
    available = sorted(data.clean.time.dropna().unique())
    teams = tuple(sorted(set(request.args.getlist("time") or GROUP_TEAMS)))
    variable = request.args.get("variavel", "pontos")
    metric = request.args.get("medida", "média")
    if not teams or any(t not in available for t in teams):
        abort(400, description="Seleção de times inválida.")
    if variable not in VARIABLES or metric not in METRICS:
        abort(400, description="Variável ou medida inválida.")
    return path, modified, data, available, teams, variable, metric


@bp.get("/")
def index():
    return redirect("/projeto-1/")


@bp.get("/assets/plotly.js")
def plotly_asset():
    # Sem CDN: os gráficos funcionam também sem internet.
    return Response(
        get_plotlyjs(),
        mimetype="application/javascript",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@bp.get("/projeto-1/")
def report():
    path, modified, data, available, teams, variable, metric = selection()
    frame, stats, counts, records = _analysis(str(path), modified, teams)
    dictionary = pd.DataFrame(
        [
            {
                "original": original,
                "campo tratado": spec.name,
                "significado": spec.description,
                "tipo": spec.kind,
                "unidade": spec.unit,
            }
            for original, spec in SCHEMA.items()
        ]
    )
    displays = {
        "dictionary": table(dictionary),
        "quality": table(data.quality),
        "changes": table(data.changes),
        "stats": table(stats.drop(columns="campo")),
        "counts": table(counts),
        "records": table(records[records.campo == variable]),
        "cv": table(stats.pivot(index="variável", columns="time", values="CV (%)").reset_index()),
        "iqr": table(stats.pivot(index="variável", columns="time", values="IQR").reset_index()),
        "quartiles": table(
            stats[
                [
                    "time",
                    "variável",
                    "Q1",
                    "Q3",
                    "IQR",
                    "amplitude",
                    "desvio padrão",
                    "DP sem extremos IQR",
                ]
            ]
        ),
    }
    highlights = []
    for team, group in stats.groupby("time"):
        for measure, label in [
            ("CV (%)", "maior dispersão relativa"),
            ("IQR", "maior IQR bruto (unidades distintas)"),
            ("assimetria", "maior assimetria absoluta"),
        ]:
            values = group[measure].abs() if measure == "assimetria" else group[measure]
            if values.notna().any():
                r = group.loc[values.idxmax()]
                highlights.append(f"{team}: {label} em {r['variável']} ({r[measure]:.2f}).")
    return render_template(
        "report.html",
        data=data,
        frame=frame,
        available=available,
        teams=teams,
        variables=VARIABLES,
        variable=variable,
        metric=metric,
        metrics=METRICS,
        tables=displays,
        box=Markup(boxplot(frame, variable)),
        hist=Markup(histogram(frame, variable)),
        bars=Markup(comparison(frame, variable, metric)),
        interpretations=interpretations(stats, variable),
        highlights=highlights,
        features=list(model_features(frame).columns),
        source_missing=int(data.raw.isna().sum().sum()),
        clean_missing=int(data.clean.isna().sum().sum()),
    )


@bp.get("/projeto-1/exportar/<kind>.csv")
def export(kind):
    path, modified, data, _, teams, _, _ = selection()
    frame, stats, counts, records = _analysis(str(path), modified, teams)
    options = {
        "dados": frame,
        "estatisticas": stats,
        "outliers": records,
        "contagens": counts,
        "qualidade": data.quality,
        "atributos": model_features(frame),
    }
    if kind not in options:
        abort(404)
    return Response(
        options[kind].to_csv(index=False, decimal=",", sep=";"),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{kind}.csv"'},
    )
