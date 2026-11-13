"""BioSpace : suivi local de santé et consultation facultative des données NASA OSDR."""
import logging

import streamlit as st

from src import applog, demo, storage
from src.config import SCENARIO_FOCUS, SCENARIO_NAMES
from src.detector import (
    BASELINE_DAYS, DOMAINS, ORANGE, RED, WINDOW,
    compute_zscores, current_scores, current_status,
)
from src.tracker import STATES
from src.ui import CSS, banner, header
from src.views import (
    actions_view, checkin, method, nasa_data, overview, report_view, trends, validation_view,
)
from src.views.context import build_context

applog.setup()
log = logging.getLogger("biospace")

st.set_page_config(page_title="BioSpace · Copilote santé de l'équipage", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

conn = storage.connect()


def safe(name, render, ctx):
    """Une erreur dans une vue ne doit jamais faire tomber toute l'application."""
    try:
        render(ctx)
    except Exception:
        log.exception("Erreur dans la vue %s", name)
        st.error(f"Impossible d'afficher « {name} ». L'erreur a été enregistrée dans le journal "
                 f"({applog.log_path()}). Le reste de l'application reste utilisable.")


# --- Barre latérale : profils ---
st.sidebar.title("BioSpace")
astronauts = storage.list_astronauts(conn)

with st.sidebar.expander("Nouveau profil", expanded=not astronauts):
    new_name = st.text_input("Nom de l'astronaute", key="new_name", placeholder="Ex. : Cdt. Dupont")
    kind = st.radio("Type", ["Profil réel (saisie et import)", "Démonstration (scénario simulé)"],
                    key="new_kind")
    scenario_new = None
    if kind.startswith("Démo"):
        scenario_new = st.selectbox("Scénario", list(SCENARIO_NAMES), format_func=SCENARIO_NAMES.get,
                                    key="new_scenario")
    if st.button("Créer le profil", key="create_profile"):
        try:
            aid = storage.create_astronaut(conn, new_name, is_demo=bool(scenario_new), scenario=scenario_new)
            if scenario_new:
                demo.load_scenario(conn, aid, scenario_new, SCENARIO_FOCUS.get(scenario_new, BASELINE_DAYS))
            st.session_state["current_id"] = aid
            st.session_state["flash"] = f"Profil « {new_name.strip()} » créé."
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))

if not astronauts:
    st.markdown(header("Bio<span>Space</span> · Suivi de santé de l'équipage",
                       "Bienvenue : crée un premier profil dans la barre latérale."),
                unsafe_allow_html=True)
    st.info("Pour une démonstration immédiate, crée un profil de type « Démonstration ». "
            "Pour un usage réel, crée un profil réel puis saisis un bilan quotidien ou importe un CSV.")
    start_tab, nasa_tab = st.tabs(["Démarrer", "Données NASA"])
    with start_tab:
        st.markdown(
            "Crée un profil dans la barre latérale pour accéder au suivi quotidien, "
            "aux tendances, aux alertes et aux rapports."
        )
    with nasa_tab:
        safe("Données NASA", nasa_data.render, None)
    st.stop()

ids = [a["id"] for a in astronauts]
if st.session_state.get("current_id") not in ids:
    st.session_state["current_id"] = ids[-1]
current_id = st.sidebar.selectbox(
    "Astronaute", ids, key="current_id",
    format_func=lambda i: next(a["name"] + (" (démo)" if a["is_demo"] else "") for a in astronauts if a["id"] == i),
)
astronaut = storage.get_astronaut(conn, current_id)

# --- Contrôles du mode démonstration ---
if astronaut["is_demo"]:
    st.sidebar.markdown("**Mode démonstration**")
    st.sidebar.caption(f"Scénario : {SCENARIO_NAMES[astronaut['scenario']]}")
    day_now = demo.mission_day(conn, current_id)
    total = demo.scenario_length(astronaut["scenario"])
    c1, c2, c3 = st.sidebar.columns(3)
    for col, n, label in ((c1, 1, "+1 j"), (c2, 7, "+7 j"), (c3, 30, "+30 j")):
        if col.button(label, key=f"adv{n}", disabled=day_now >= total, width="stretch"):
            demo.advance(conn, current_id, n)
            st.rerun()
    st.sidebar.caption(f"Jour {day_now} sur {total}.")
    if st.sidebar.button("Rejouer le scénario", key="replay", width="stretch"):
        demo.load_scenario(conn, current_id, astronaut["scenario"],
                           SCENARIO_FOCUS.get(astronaut["scenario"], BASELINE_DAYS))
        st.rerun()

# --- Contexte et suivi des alertes ---
ctx = build_context(conn, astronaut)
for ch in ctx.changes:
    if ch["kind"] in ("alerte_ouverte", "alerte_aggravee", "escalade_auto"):
        label = {"alerte_ouverte": "Nouvelle alerte", "alerte_aggravee": "Alerte aggravée",
                 "escalade_auto": "Escalade automatique"}[ch["kind"]]
        st.toast(f"{label} : {ch['domain']}", icon="🔴" if ch["status"] == "rouge" else "🟠")

# --- Sauvegarde et suppression ---
with st.sidebar.expander("Données"):
    st.caption(f"Base locale : {storage.db_path()}")
    import tempfile
    from pathlib import Path
    if st.button("Préparer une sauvegarde", key="backup"):
        tmp = Path(tempfile.mkdtemp()) / "biospace_sauvegarde.db"
        storage.vacuum_backup(conn, tmp)
        st.session_state["backup_bytes"] = tmp.read_bytes()
    if "backup_bytes" in st.session_state:
        st.download_button("Télécharger la sauvegarde", st.session_state["backup_bytes"],
                           file_name="biospace_sauvegarde.db", mime="application/octet-stream")
    confirm = st.checkbox("Confirmer la suppression de ce profil", key=f"del_ok_{current_id}")
    if st.button("Supprimer ce profil", key="delete", disabled=not confirm):
        storage.delete_astronaut(conn, current_id)
        st.session_state.pop("current_id", None)
        st.rerun()
st.sidebar.caption("Données de suivi saisies ou simulées ; jeux de recherche NASA consultables séparément. Ne remplace pas un avis médical.")

# --- En-tête et bandeau de synthèse ---
st.markdown(
    header("Bio<span>Space</span> · Suivi de santé de l'équipage",
           f"{astronaut['name']} · Jour {ctx.day} · "
           f"référence personnelle calculée sur les {BASELINE_DAYS} premiers jours"),
    unsafe_allow_html=True,
)
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

n_red = sum(d["status"] == "rouge" for d in ctx.details.values())
n_orange = sum(d["status"] == "orange" for d in ctx.details.values())
escalated = [i for i in ctx.items if i["state"] == "escalade"]
if ctx.empty:
    st.markdown(banner("inconnu", "Aucune donnée : saisis un bilan ou importe un fichier"),
                unsafe_allow_html=True)
elif n_red:
    st.markdown(banner("rouge", f"{n_red} système(s) en action requise"
                       + (f" · {n_orange} à surveiller" if n_orange else "")
                       + (f" · {len(escalated)} escalade(s) vers l'équipe médicale" if escalated else "")),
                unsafe_allow_html=True)
elif n_orange:
    st.markdown(banner("orange", f"{n_orange} système(s) à surveiller"
                       + (f" · {len(escalated)} escalade(s)" if escalated else "")),
                unsafe_allow_html=True)
elif ctx.calibrating:
    st.markdown(banner("inconnu", f"Calibration en cours : jour {ctx.day} sur {BASELINE_DAYS}"),
                unsafe_allow_html=True)
else:
    st.markdown(banner("vert", "Tous les indicateurs sont dans ta normale"), unsafe_allow_html=True)

n_open = len([i for i in ctx.items if i["state"] in ("a_faire", "escalade")])
tabs = st.tabs(["Vue d'ensemble", "Bilan du jour", f"Actions ({n_open})" if n_open else "Actions",
                "Tendances", "Données NASA", "Rapport", "Validation", "Méthode"])
for tab, (name, render) in zip(tabs, [
    ("Vue d'ensemble", overview.render), ("Bilan du jour", checkin.render),
    ("Actions", actions_view.render), ("Tendances", trends.render),
    ("Données NASA", nasa_data.render), ("Rapport", report_view.render),
    ("Validation", validation_view.render),
    ("Méthode", method.render),
]):
    with tab:
        safe(name, render, ctx)
