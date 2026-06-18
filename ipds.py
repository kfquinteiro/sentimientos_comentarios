"""IPD-S — Indicador de Presença Digital (Social).

Calcula um índice de 0 a 1 por marca usando média geométrica
(metodologia IDH) de até 4 dimensões:
  1. Atividade     — posts/mês
  2. Engajamento   — interações/post
  3. Multicanal    — redes ativas / total de redes
  4. Sentimento    — % positivo (opcional, se houver dados)

Normalização min-max dentro do grupo de marcas comparadas.
"""
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go

BANDS = [
    (0.00, 0.20, "Muy bajo",  "#e74c3c"),
    (0.20, 0.40, "Bajo",      "#e67e22"),
    (0.40, 0.60, "Medio",     "#f1c40f"),
    (0.60, 0.80, "Alto",      "#2ecc71"),
    (0.80, 1.00, "Muy alto",  "#1a9850"),
]

EPSILON = 0.001


def _minmax(series):
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    return ((series - mn) / (mx - mn)).clip(EPSILON, 1.0)


def calculate(posts_df, sentiment_df=None):
    """Calcula o IPD-S por marca.

    Parameters
    ----------
    posts_df : DataFrame
        Deve ter colunas: marca, red, fecha, interacciones.
        Uma linha por post.
    sentiment_df : DataFrame, optional
        Deve ter colunas: marca, sentimiento.
        Uma linha por comentário (resultado do análise de sentimiento).

    Returns
    -------
    DataFrame com colunas: Marca, Atividade, Engajamento, Multicanal,
    Sentimento (se disponível), IPD-S, Faixa.
    """
    df = posts_df.copy()
    required = {"marca", "red", "interacciones"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError("Faltam colunas: {}".format(", ".join(missing)))

    df["interacciones"] = pd.to_numeric(df["interacciones"], errors="coerce").fillna(0)

    total_networks = df["red"].nunique()

    by_brand = df.groupby("marca").agg(
        posts=("marca", "size"),
        avg_interactions=("interacciones", "mean"),
        networks=("red", "nunique"),
    ).reset_index()

    if "fecha" in df.columns:
        df["_mes"] = pd.to_datetime(df["fecha"], errors="coerce").dt.to_period("M")
        months_in_data = df["_mes"].nunique() or 1
        posts_per_month = df.groupby("marca").size() / months_in_data
        by_brand["posts_per_month"] = by_brand["marca"].map(posts_per_month).fillna(0)
    else:
        by_brand["posts_per_month"] = by_brand["posts"]

    by_brand["d_atividade"] = _minmax(np.log1p(by_brand["posts_per_month"]))
    by_brand["d_engajamento"] = _minmax(np.log1p(by_brand["avg_interactions"]))
    by_brand["d_multicanal"] = (by_brand["networks"] / max(total_networks, 1)).clip(EPSILON, 1.0)

    dimensions = ["d_atividade", "d_engajamento", "d_multicanal"]

    if sentiment_df is not None and "sentimiento" in sentiment_df.columns and "marca" in sentiment_df.columns:
        sent = sentiment_df.copy()
        classified = sent[sent["sentimiento"].isin(["Positivo", "Negativo"])]
        if not classified.empty:
            pos_ratio = (
                classified.groupby("marca")["sentimiento"]
                .apply(lambda s: (s == "Positivo").sum() / max(len(s), 1))
            ).rename("d_sentimento")
            by_brand = by_brand.merge(pos_ratio, left_on="marca", right_index=True, how="left")
            by_brand["d_sentimento"] = by_brand["d_sentimento"].fillna(0.5).clip(EPSILON, 1.0)
            dimensions.append("d_sentimento")

    by_brand["ipds"] = by_brand[dimensions].apply(
        lambda row: math.prod(row) ** (1 / len(row)), axis=1
    ).round(3)

    def _band(v):
        for lo, hi, label, _ in BANDS:
            if v < hi or hi == 1.00:
                return label
        return BANDS[-1][2]

    by_brand["faixa"] = by_brand["ipds"].apply(_band)

    result = by_brand[["marca"] + dimensions + ["ipds", "faixa"]].copy()
    rename = {
        "marca": "Marca",
        "d_atividade": "Atividade",
        "d_engajamento": "Engajamento",
        "d_multicanal": "Multicanal",
        "ipds": "IPD-S",
        "faixa": "Faixa",
    }
    if "d_sentimento" in result.columns:
        rename["d_sentimento"] = "Sentimento"
    result = result.rename(columns=rename)
    return result.sort_values("IPD-S", ascending=False).reset_index(drop=True)


def thermometer_fig(ipds_df):
    """Cria o termômetro horizontal do IPD-S (estilo da imagem de referência)."""
    fig = go.Figure()

    for lo, hi, label, color in BANDS:
        fig.add_shape(
            type="rect", x0=lo, x1=hi, y0=0, y1=1,
            fillcolor=color, opacity=0.25, line_width=0,
            layer="below",
        )

    sorted_df = ipds_df.sort_values("IPD-S").reset_index(drop=True)
    n = len(sorted_df)
    for i, (_, row) in enumerate(sorted_df.iterrows()):
        score = row["IPD-S"]
        marca = row["Marca"]
        band_color = "#95a5a6"
        for lo, hi, _, color in BANDS:
            if score < hi or hi == 1.00:
                band_color = color
                break
        y_pos = 0.3 + (i / max(n - 1, 1)) * 0.9 if n > 1 else 0.7
        fig.add_trace(go.Scatter(
            x=[score], y=[y_pos],
            mode="markers+text",
            marker=dict(size=20, color=band_color,
                        line=dict(width=2, color="white")),
            text=["<b>{}</b>  {}".format(marca, score)],
            textposition="top center",
            textfont=dict(size=11),
            hovertemplate="{}: {}<extra></extra>".format(marca, score),
            showlegend=False,
        ))

    for _, _, label, color in BANDS:
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=12, color=color),
            name=label, showlegend=True,
        ))

    fig.update_layout(
        title="Termômetro Digital do IPD-S",
        xaxis=dict(
            range=[-0.02, 1.02],
            tickmode="linear", tick0=0, dtick=0.05,
        ),
        yaxis=dict(visible=False, range=[-0.2, 2.2]),
        height=400,
        legend=dict(orientation="h", yanchor="top", y=-0.12,
                    xanchor="center", x=0.5),
        margin=dict(t=60, b=100),
    )
    return fig


def dimensions_bar_fig(ipds_df):
    """Gráfico de barras agrupadas mostrando cada dimensão por marca."""
    dims = [c for c in ["Atividade", "Engajamento", "Multicanal", "Sentimento"]
            if c in ipds_df.columns]
    if not dims:
        return None
    melted = ipds_df.melt(id_vars="Marca", value_vars=dims,
                          var_name="Dimensión", value_name="Valor")
    import plotly.express as px
    fig = px.bar(
        melted, x="Marca", y="Valor", color="Dimensión",
        barmode="group", title="Dimensões do IPD-S por marca",
        labels={"Valor": "Índice (0-1)", "Dimensión": "Dimensão"},
    )
    fig.update_layout(yaxis=dict(range=[0, 1.05]))
    return fig
