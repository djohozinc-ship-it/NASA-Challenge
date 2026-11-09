"""Tendances : mesure, moyenne glissante, plage normale et score de danger."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from src.config import DIRECTION, DOMAINS, LABELS, UNITS
from src.detector import BASELINE_DAYS, ORANGE, RED, WINDOW, danger_score
from src.ui import COLORS


def render(ctx):
    if ctx.empty:
        st.info("Aucune donnée à afficher.")
        return
    indicator = st.selectbox("Indicateur", list(DOMAINS), key=f"trend_{ctx.aid}",
                             format_func=lambda c: f"{DOMAINS[c]} · {LABELS[c]}")
    df = ctx.df
    series = df[indicator]
    if series.notna().sum() == 0:
        st.info("Aucune mesure pour cet indicateur.")
        return

    title = f"{LABELS[indicator]} ({UNITS[indicator]})".replace(" ()", "")
    fig = go.Figure()
    if not ctx.calibrating:
        base = df.iloc[:BASELINE_DAYS][indicator]
        mean, std = base.mean(), base.std()
        half = ORANGE * std * np.sqrt(1 / WINDOW + 1 / base.count())
        fig.add_hrect(y0=mean - half, y1=mean + half, fillcolor=COLORS["vert"], opacity=0.10, line_width=0)
        fig.add_vline(x=df["date"].iloc[BASELINE_DAYS - 1].to_pydatetime(),
                      line_dash="dot", line_color="#8FA0BC")
    fig.add_trace(go.Scatter(x=df["date"], y=series, mode="lines", name="Mesure quotidienne",
                             line=dict(color="#5B6B85", width=1), connectgaps=False))
    fig.add_trace(go.Scatter(x=df["date"], y=series.rolling(WINDOW, min_periods=4).mean(),
                             mode="lines", name=f"Moyenne {WINDOW} jours",
                             line=dict(color="#4F8BF9", width=3)))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", height=380, yaxis_title=title,
                      legend=dict(orientation="h", y=1.12), margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Zone verte : plage normale de la moyenne 7 jours (seuil orange). "
               "Pointillé : fin de la période de référence.")

    if not ctx.calibrating:
        score = danger_score(ctx.z[indicator], DIRECTION[indicator])
        f2 = go.Figure()
        f2.add_trace(go.Scatter(x=ctx.z["date"], y=score, mode="lines", name="Score de danger",
                                line=dict(color="#F39C12", width=2)))
        for level, label, color in ((ORANGE, "Seuil orange", COLORS["orange"]),
                                    (RED, "Seuil rouge", COLORS["rouge"])):
            f2.add_hline(y=level, line_dash="dot", line_color=color,
                         annotation_text=label, annotation_position="top left")
        f2.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                         plot_bgcolor="rgba(0,0,0,0)", height=240, showlegend=False,
                         yaxis_title="Score de danger", margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(f2, width="stretch")
        st.caption("Un état orange ou rouge exige que le score dépasse le seuil 3 jours de suite.")

    st.download_button("Exporter les z-scores (CSV)", ctx.z.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"zscores_{ctx.astronaut['name']}.csv", mime="text/csv")
