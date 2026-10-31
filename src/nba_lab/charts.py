"""Gráficos com as mesmas convenções numéricas usadas nas tabelas."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import gaussian_kde

from .analysis import describe
from .schema import VARIABLES

COLORS = ["#176b87", "#e37735", "#725ac1", "#2b8a6e", "#b04666"]


def html(fig: go.Figure, title: str, y: str, x: str = "Time") -> str:
    fig.update_layout(
        title=title,
        xaxis_title=x,
        yaxis_title=y,
        template="plotly_white",
        height=550,
        margin=dict(t=80, b=100, r=220),
        legend=dict(orientation="v", x=1.02, y=1, font=dict(size=11)),
        showlegend=True,
        font=dict(family="Arial", size=13),
    )
    return fig.to_html(
        full_html=False, include_plotlyjs=False, config={"responsive": True, "displaylogo": False}
    )


def boxplot(frame: pd.DataFrame, variable: str) -> str:
    fig = go.Figure()
    for i, (team, group) in enumerate(frame.groupby("time")):
        x = group[variable].dropna()
        if x.empty:
            continue
        d = describe(x)
        inside = x[x.between(d["limite inferior"], d["limite superior"])]
        # Fornecer quartis e bigodes impede divergência entre Plotly e pandas.
        fig.add_trace(
            go.Box(
                name=team,
                x=[team],
                q1=[d["Q1"]],
                median=[d["mediana"]],
                q3=[d["Q3"]],
                lowerfence=[inside.min()],
                upperfence=[inside.max()],
                marker_color=COLORS[i % len(COLORS)],
                boxpoints=False,
                showlegend=True,
            )
        )
        elements = [
            ("Média", [d["média"]], "diamond"),
            ("Mediana", [d["mediana"]], "line-ew"),
            ("Q1", [d["Q1"]], "triangle-up"),
            ("Q3", [d["Q3"]], "triangle-down"),
            ("Limite inferior 1,5 IQR", [d["limite inferior"]], "line-ew"),
            ("Limite superior 1,5 IQR", [d["limite superior"]], "line-ew"),
            ("Outliers inferiores", x[x < d["limite inferior"]].tolist(), "x"),
            ("Outliers superiores", x[x > d["limite superior"]].tolist(), "x"),
        ]
        if x.value_counts().max() > 1:
            elements.append(("Moda(s)", x.mode().tolist(), "star"))
        for name, values, symbol in elements:
            fig.add_trace(
                go.Scatter(
                    x=[team] * len(values),
                    y=values,
                    mode="markers",
                    name=name,
                    legendgroup=name,
                    showlegend=i == 0,
                    marker=dict(symbol=symbol, size=10),
                    hovertemplate=f"{team} · {name}: %{{y:.2f}}<extra></extra>",
                )
            )
    unit = "pontos por jogo" if variable == "pontos" else "ocorrências por jogo"
    return html(fig, f"Boxplot · {VARIABLES[variable]}", unit)


def histogram(frame: pd.DataFrame, variable: str) -> str:
    fig = go.Figure()
    for i, (team, group) in enumerate(frame.groupby("time")):
        x = group[variable].dropna()
        if x.empty:
            continue
        color = COLORS[i % len(COLORS)]
        fig.add_trace(
            go.Histogram(
                x=x,
                histnorm="probability density",
                name=f"{team} · histograma",
                opacity=0.35,
                marker_color=color,
            )
        )
        if len(x) > 1 and x.nunique() > 1:
            grid = np.linspace(max(0, x.min() - x.std()), x.max() + x.std(), 250)
            fig.add_trace(
                go.Scatter(
                    x=grid,
                    y=gaussian_kde(x)(grid),
                    mode="lines",
                    name=f"{team} · KDE (Scott)",
                    line=dict(color=color),
                )
            )
    fig.update_layout(barmode="overlay")
    return html(
        fig,
        f"Histograma e densidade · {VARIABLES[variable]}",
        "Densidade (1/unidade)",
        "Pontos por jogo" if variable == "pontos" else "Ocorrências por jogo",
    )


def comparison(frame: pd.DataFrame, variable: str, metric: str) -> str:
    rows = []
    pooled = frame[variable]
    sd = pooled.std(ddof=1)
    for team, group in frame.groupby("time"):
        d = describe(group[variable])
        if d["n"] == 0:
            continue
        value = (
            ((d["média"] - pooled.mean()) / sd if sd > 0 else 0)
            if metric == "z médio"
            else d[metric]
        )
        rows.append((team, value))
    fig = go.Figure(
        go.Bar(
            x=[x[0] for x in rows],
            y=[x[1] for x in rows],
            name=metric,
            marker_color=COLORS[0],
            text=[f"{x[1]:.2f}" for x in rows],
            textposition="auto",
        )
    )
    units = (
        "percentual (%)"
        if metric == "CV (%)"
        else (
            "desvios padrão do conjunto selecionado"
            if metric == "z médio"
            else "pontos por jogo"
            if variable == "pontos"
            else "ocorrências por jogo"
        )
    )
    return html(fig, f"Comparação · {VARIABLES[variable]} · {metric}", units)
