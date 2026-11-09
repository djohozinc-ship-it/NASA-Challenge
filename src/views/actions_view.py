"""Alertes ouvertes et cartes d'action suivies."""
import pandas as pd
import streamlit as st

from src.actions import ACTIONS
from src.config import ESCALATION_DAYS, LABELS
from src.detector import ORANGE
from src.summary import with_unit
from src.tracker import STATES, all_items, days_open, set_state
from src.ui import badge, state_chip


def _item_card(ctx, item):
    info = ctx.details.get(item["domain"], {})
    advice = ACTIONS[item["domain"]]
    age = days_open(item, ctx.as_of)
    icon = "🔴" if item["status"] == "rouge" else "🟠"
    with st.expander(f"{icon} {item['domain']} · ouverte depuis {age} jour(s)",
                     expanded=item["status"] == "rouge" or item["state"] == "escalade"):
        st.markdown(badge(item["status"]) + " &nbsp; " + state_chip(item["state"], STATES[item["state"]]),
                    unsafe_allow_html=True)
        if item["state"] == "escalade":
            st.error("Aucune action enregistrée dans le délai : l'équipe médicale doit être informée. "
                     "Utilise « Signaler à l'équipe médicale » une fois le contact établi.")
        st.write(f"**Pourquoi :** {advice['why']}")

        for hit in info.get("critical", []):
            sign = "<" if hit["value"] < hit["limit"] else ">"
            st.error(f"Seuil critique : {LABELS[hit['indicator']]} "
                     f"{with_unit(hit['value'], hit['indicator'])} "
                     f"({sign} {with_unit(hit['limit'], hit['indicator'])}) le {hit['date']:%d/%m/%Y}")
        flagged = [(c, s) for c, s in info.get("drivers", []) if s >= ORANGE]
        if flagged:
            st.write("**Indicateurs en cause :**")
            for c, s in flagged:
                st.markdown(f"- {LABELS[c]} : {with_unit(ctx.recent[c], c)} "
                            f"(référence {with_unit(ctx.reference[c], c)}), score de danger {s:.1f}")
        st.write("**Que faire :**")
        for step in advice["steps"]:
            st.markdown(f"- {step}")

        note = st.text_input("Note (facultatif)", key=f"note_{item['id']}",
                             placeholder="Ex. : séance reprise, appel au médecin de vol à 14 h")
        b1, b2, b3 = st.columns(3)
        for col, state, label in ((b1, "fait", "Marquer comme fait"),
                                  (b2, "reporte", "Reporter"),
                                  (b3, "signale", "Signaler à l'équipe médicale")):
            if col.button(label, key=f"{state}_{item['id']}", width="stretch"):
                set_state(ctx.conn, ctx.aid, item["id"], state, ctx.as_of, note)
                st.rerun()
        st.caption(f"Escalade automatique si aucune action sous "
                   f"{ESCALATION_DAYS[item['status']]} jour(s) ({item['status']}).")


def render(ctx):
    if ctx.empty:
        st.info("Aucune donnée : pas d'alerte à suivre.")
        return
    if not ctx.items:
        st.success("Aucune action nécessaire : tout est dans ta normale personnelle.")
    for item in ctx.items:
        _item_card(ctx, item)

    history = [i for i in all_items(ctx.conn, ctx.aid) if i["state"] == "resolue"]
    if history:
        with st.expander(f"Historique : {len(history)} alerte(s) résolue(s)"):
            table = pd.DataFrame([{
                "Système": i["domain"], "Gravité max.": i["status"],
                "Ouverte": i["opened"], "Résolue": i["closed"], "Note": i["note"] or "",
            } for i in history])
            st.dataframe(table, hide_index=True, width="stretch")
    st.caption("Conseils généraux de démonstration, pas des protocoles médicaux.")
