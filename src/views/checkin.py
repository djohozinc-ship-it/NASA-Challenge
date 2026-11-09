"""Bilan du jour (saisie guidée) et import de fichiers CSV."""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.config import DOMAIN_ORDER, INDICATORS, LABELS, UNITS, VALID
from src.ingest import add_checkin, import_csv
from src.summary import with_unit

STEPS = {"/10": 0.5, "min/j": 5.0, "bpm": 1.0, "ms": 1.0, "mmHg": 1.0, "kg": 0.1,
         "g/dL": 0.1, "°C": 0.1, "mSv/j": 0.01, "h": 0.25, "": 0.01}
FORMATS = {"/10": "%.1f", "min/j": "%.0f", "bpm": "%.0f", "ms": "%.0f", "mmHg": "%.0f",
           "kg": "%.1f", "g/dL": "%.1f", "°C": "%.1f", "mSv/j": "%.2f", "h": "%.2f", "": "%.2f"}

TEMPLATE = ("date," + ",".join(INDICATORS) + "\n2026-01-01," +
            ",".join("" for _ in INDICATORS) + "\n").encode("utf-8")


def _default_date(ctx):
    if ctx.as_of is not None:
        return (ctx.as_of + timedelta(days=1)).date()
    return date.today()


def _field(indicator, ctx):
    low, high = VALID[indicator]
    unit = UNITS[indicator]
    help_ = None
    if not ctx.empty and not pd.isna(ctx.reference.get(indicator)):
        help_ = f"Ta référence : {with_unit(ctx.reference[indicator], indicator)}"
    return st.number_input(
        LABELS[indicator] + (f" ({unit})" if unit else ""),
        min_value=float(low), max_value=float(high), value=None,
        step=STEPS.get(unit, 0.1), format=FORMATS.get(unit, "%.2f"),
        key=f"ci_{ctx.aid}_{indicator}", help=help_, placeholder="non mesuré",
    )


def render(ctx):
    st.markdown("##### Bilan du jour")
    st.caption("Renseigne ce que tu as mesuré ou ressenti aujourd'hui. Les champs vides sont ignorés : "
               "un bilan partiel est valable. Une saisie sur une date existante la remplace.")

    with st.form(f"checkin_{ctx.aid}", clear_on_submit=False):
        day = st.date_input("Date du bilan", value=_default_date(ctx), key=f"ci_date_{ctx.aid}")
        left, right = st.columns(2)
        values = {}
        with left:
            st.markdown("**Ressenti et questionnaires**")
            for c, meta in INDICATORS.items():
                if meta["source"] == "saisie":
                    values[c] = _field(c, ctx)
        with right:
            st.markdown("**Mesures physiologiques**")
            for c, meta in INDICATORS.items():
                if meta["source"] == "auto":
                    values[c] = _field(c, ctx)
        submitted = st.form_submit_button("Enregistrer le bilan", type="primary")

    if submitted:
        written, errors = add_checkin(ctx.conn, ctx.aid, day, values)
        if errors:
            for e in errors:
                st.error(e)
        else:
            st.session_state["flash"] = f"Bilan du {day:%d/%m/%Y} enregistré ({written} valeur(s))."
            for c in INDICATORS:
                st.session_state.pop(f"ci_{ctx.aid}_{c}", None)
            st.rerun()

    st.divider()
    st.markdown("##### Importer des données (CSV)")
    st.caption("Une ligne par jour. Colonne `date` obligatoire, puis une colonne par indicateur "
               "(séparateur virgule ou point-virgule, virgule décimale acceptée). Les valeurs hors "
               "bornes plausibles sont rejetées et listées.")
    c1, c2 = st.columns([3, 1])
    up = c1.file_uploader("Fichier CSV", type=["csv", "txt"], key=f"up_{ctx.aid}",
                          label_visibility="collapsed")
    c2.download_button("Modèle CSV", TEMPLATE, file_name="modele_biospace.csv", mime="text/csv")
    if up is not None and st.button("Importer ce fichier", key=f"imp_{ctx.aid}"):
        report = import_csv(ctx.conn, ctx.aid, up.getvalue(), up.name)
        if report.ok:
            st.success(f"{report.values_imported} valeur(s) importée(s) sur {report.rows_imported} jour(s).")
        else:
            st.error("Aucune valeur importée.")
        for w in report.warnings:
            st.warning(w)
        if report.rejected:
            with st.expander(f"{len(report.rejected)} rejet(s)"):
                for line, why in report.rejected[:100]:
                    st.write(f"Ligne {line} : {why}" if line else why)
        if report.ok:
            st.session_state["flash"] = f"Import terminé : {report.values_imported} valeur(s)."
            st.rerun()
