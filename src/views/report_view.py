"""Rapports pour l'équipe médicale et journal des événements."""
import pandas as pd
import streamlit as st

from src import report, storage, tracker
from src.report import EVENT_FR


def _safe_name(name):
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name).strip("_") or "astronaute"


def render(ctx):
    if ctx.empty:
        st.info("Aucune donnée : le rapport sera disponible après la première mesure.")
        return
    st.markdown("##### Rapport pour l'équipe médicale")
    st.caption("Un document prêt à transmettre quand la liaison sol revient : état par système, alertes et "
               "actions, indicateurs, tendances, journal. Généré localement.")
    key = f"pdf_{ctx.aid}_{ctx.as_of:%Y%m%d}_{len(ctx.items)}"
    c1, c2, c3 = st.columns(3)
    if c1.button("Générer le rapport PDF", type="primary", width="stretch"):
        with st.spinner("Génération du rapport..."):
            st.session_state[key] = report.build_pdf(
                ctx.astronaut, ctx.df, ctx.z, ctx.details,
                tracker.all_items(ctx.conn, ctx.aid), storage.list_events(ctx.conn, ctx.aid, 40),
                ctx.as_of)
    base = f"biospace_{_safe_name(ctx.astronaut['name'])}_{ctx.as_of:%Y%m%d}"
    if key in st.session_state:
        c1.download_button("Télécharger le PDF", st.session_state[key], file_name=f"{base}.pdf",
                           mime="application/pdf", width="stretch")
    c2.download_button("Mesures (CSV)", report.measurements_csv(ctx.df),
                       file_name=f"{base}_mesures.csv", mime="text/csv", width="stretch")
    events = storage.list_events(ctx.conn, ctx.aid, 1000)
    c3.download_button("Journal (CSV)", report.events_csv(events),
                       file_name=f"{base}_journal.csv", mime="text/csv", width="stretch")

    st.markdown("##### Journal des événements")
    if not events:
        st.caption("Aucun événement pour l'instant.")
        return
    table = pd.DataFrame([{
        "Date mission": e["date"], "Événement": EVENT_FR.get(e["kind"], e["kind"]),
        "Système": e["domain"] or "", "Gravité": e["status"] or "", "Détail": e["detail"] or "",
    } for e in events[:200]])
    st.dataframe(table, hide_index=True, width="stretch", height=360)
