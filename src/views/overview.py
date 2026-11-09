"""Vue d'ensemble : radar, alertes prioritaires et fiches par système."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import DOMAIN_ORDER, DOMAINS, LABELS
from src.detector import BASELINE_DAYS, ORANGE, RED, to_status
from src.summary import fmt, with_unit
from src.ui import COLORS, alert_item, all_clear, autonomy_card, status_card


def _radar(ctx):
    scores = {d: 0.0 if pd.isna(v["score"]) else max(0.0, v["score"])
              for d, v in ctx.details.items()}
    names, vals = list(scores), list(scores.values())
    worst = max(vals) if vals else 0
    color = COLORS["rouge"] if worst >= RED else COLORS["orange"] if worst >= ORANGE else COLORS["vert"]
    axis_max = max(5, min(worst * 1.15, 12))
    fig = go.Figure()
    for level, label in ((ORANGE, "Seuil orange"), (RED, "Seuil rouge")):
        fig.add_trace(go.Scatterpolar(
            r=[level] * (len(names) + 1), theta=names + names[:1], mode="lines",
            line=dict(color="#5B6B85", dash="dot", width=1), name=label, hoverinfo="skip"))
    fig.add_trace(go.Scatterpolar(
        r=vals + vals[:1], theta=names + names[:1], fill="toself", name="Ton état",
        line=dict(color=color, width=3), fillcolor=color + "33"))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=400,
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(range=[0, axis_max], showticklabels=False)),
        legend=dict(orientation="h", y=-0.1), margin=dict(l=100, r=100, t=20, b=20))
    return fig


def _alert_detail(ctx, domain, info):
    if info["critical"]:
        hit = info["critical"][0]
        sign = "<" if hit["value"] < hit["limit"] else ">"
        return (f"Seuil critique : {LABELS[hit['indicator']]} "
                f"{with_unit(hit['value'], hit['indicator'])} ({sign} {with_unit(hit['limit'], hit['indicator'])})")
    driver = info["driver"]
    return (f"Indicateur en cause : {LABELS[driver]} "
            f"({with_unit(ctx.recent[driver], driver)} "
            f"contre {with_unit(ctx.reference[driver], driver)} en référence)")


def render(ctx):
    if ctx.empty:
        st.info("Aucune donnée pour ce profil. Ouvre l'onglet **Bilan du jour** pour saisir une première "
                "mesure, ou importe un fichier CSV. En mode démonstration, utilise la barre latérale.")
        return

    if ctx.calibrating:
        st.markdown("##### Calibration de ta référence personnelle")
        st.progress(ctx.progress, text=f"Jour {ctx.day} sur {BASELINE_DAYS} : le système apprend ta normale. "
                                        "Les alertes statistiques démarrent à la fin de cette période. "
                                        "Les seuils critiques restent actifs.")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Jour de mission", ctx.day)
    k2.metric("Systèmes en alerte", ctx.n_alerts)
    k3.metric("Dose cumulée", f"{ctx.df['dose_cumulative'].iloc[-1]:.1f} mSv")
    k4.metric("Dernière mesure", ctx.as_of.strftime("%d/%m/%Y"))

    left, right = st.columns([1, 1.1])
    left.plotly_chart(_radar(ctx), width="stretch")
    with right:
        st.markdown("##### Alertes prioritaires")
        alerting = [(d, v) for d, v in ctx.details.items() if v["status"] in ("rouge", "orange")]
        alerting.sort(key=lambda t: (t[1]["status"] != "rouge", -(t[1]["score"] or 0)))
        if not alerting:
            msg = ("Calibration en cours : aucune alerte statistique pour l'instant."
                   if ctx.calibrating else "Aucune alerte : tout est dans ta normale personnelle.")
            st.markdown(all_clear(msg), unsafe_allow_html=True)
        for d, v in alerting:
            st.markdown(alert_item(d, v["status"], _alert_detail(ctx, d, v)), unsafe_allow_html=True)
        pending = [i for i in ctx.items if i["state"] in ("a_faire", "escalade")]
        if pending:
            st.caption(f"{len(pending)} action(s) en attente : voir l'onglet **Actions**.")

    st.markdown("##### Systèmes physiologiques")
    by_domain = {}
    for r in ctx.rows:
        by_domain.setdefault(r["domain"], []).append(r)
    grid = DOMAIN_ORDER + [None]   # dernière case : carte d'autonomie
    for i in range(0, len(grid), 4):
        cols = st.columns(4)
        for col, domain in zip(cols, grid[i:i + 4]):
            if domain is None:
                col.markdown(autonomy_card(), unsafe_allow_html=True)
                continue
            rows = [{"label": r["label"], "unit": r["unit"],
                     "value": fmt(r["value"], r["indicator"]),
                     "ref": fmt(r["reference"], r["indicator"]),
                     "status": r["status"]} for r in by_domain[domain]]
            col.markdown(status_card(domain, ctx.details[domain]["status"], rows), unsafe_allow_html=True)
