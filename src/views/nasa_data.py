"""Vue de consultation des données humaines NASA OSDR et des sources physiologiques NLSP."""
import streamlit as st

from src import nasa_osdr


STUDIES = {
    "OSD-575 — Inspiration4 : sérum, métabolisme et cytokines": "575",
    "OSD-569 — Inspiration4 : sang total": "569",
    "OSD-570 — Inspiration4 : cellules immunitaires PBMC": "570",
    "OSD-571 — Inspiration4 : plasma": "571",
    "OSD-53 — Expression génique chez six astronautes": "53",
    "OSD-484 — Exosomes plasmatiques de trois astronautes": "484",
}


@st.cache_data(ttl=3600, show_spinner=False)
def _metadata(study_id):
    return nasa_osdr.study_metadata(study_id)


@st.cache_data(ttl=3600, show_spinner=False)
def _files(study_id):
    return nasa_osdr.study_files(study_id)


@st.cache_data(ttl=1800, show_spinner=False)
def _archive_members(file_record):
    return nasa_osdr.archive_members(file_record)


@st.cache_data(ttl=1800, show_spinner=False)
def _preview(file_record, member=None):
    return nasa_osdr.download_table_file(file_record, member=member)


def _render_biology():
    st.markdown("#### Données biologiques humaines")
    st.caption(
        "Jeux de données humains issus de recherches spatiales. Les missions commerciales "
        "et les astronautes professionnels sont identifiés séparément."
    )
    label = st.selectbox("Étude NASA OSDR", list(STUDIES), index=0, key="nasa_study")
    study_id = STUDIES[label]
    st.markdown(
        f"[Ouvrir la fiche officielle OSDR](https://osdr.nasa.gov/bio/repo/data/studies/OSD-{study_id})"
    )

    # Streamlit réexécute cet onglet à chaque clic dans l'application : sans ce garde-fou, un
    # réseau indisponible bloquerait chaque interaction jusqu'au délai d'attente. Le chargement
    # se fait donc à la demande et un échec est mémorisé (pas de nouvelle tentative automatique).
    loaded_key, error_key = f"nasa_loaded_{study_id}", f"nasa_error_{study_id}"
    if not st.session_state.get(loaded_key):
        if st.session_state.get(error_key):
            st.warning(st.session_state[error_key])
            st.info("La fiche officielle reste consultable via le lien ci-dessus. "
                    "Diagnostic détaillé : `python -m src.nasa_osdr`.")
        label_btn = "Réessayer" if st.session_state.get(error_key) else "Charger cette étude depuis NASA OSDR"
        if st.button(label_btn, type="primary", key=f"nasa_load_{study_id}"):
            try:
                with st.spinner("Récupération depuis NASA OSDR..."):
                    _metadata(study_id)
                    _files(study_id)
                st.session_state[loaded_key] = True
                st.session_state.pop(error_key, None)
            except nasa_osdr.OSDRError as exc:
                st.session_state[error_key] = str(exc)
            st.rerun()
        return

    metadata, files = _metadata(study_id), _files(study_id)   # déjà en cache : instantané
    st.success(f"Données OSDR chargées pour OSD-{study_id}.")
    if st.checkbox("Afficher les métadonnées complètes de l'étude", key=f"nasa_meta_{study_id}"):
        st.json(metadata)    # volumineux : envoyé au navigateur seulement si demandé

    if not files:
        st.info("L'API n'a retourné aucun fichier public sur cette page. Consultez la section Files de la fiche OSDR.")
        return

    st.markdown(f"**{len(files)} fichier(s) référencé(s) sur cette page de l'API**")
    for index, item in enumerate(files):
        size = item.get("size")
        size_text = f"{size} octets" if size else "taille non renseignée"
        st.markdown(f"**{item['name']}** · {size_text}")
        st.markdown(f"[Télécharger depuis NASA OSDR]({item['download_url']})")
        filename = str(item["name"]).lower()
        if filename.endswith(".zip"):
            archive_state_key = f"nasa_members_{study_id}_{index}"
            if archive_state_key not in st.session_state:
                if st.button("Explorer cette archive", key=f"nasa_archive_{study_id}_{index}"):
                    try:
                        with st.spinner("Inventaire du contenu de l'archive..."):
                            st.session_state[archive_state_key] = _archive_members(item)
                    except nasa_osdr.OSDRError as exc:
                        st.warning(str(exc))
                        st.session_state[archive_state_key] = []
            members = st.session_state.get(archive_state_key, [])
            if members:
                member = st.selectbox(
                    "Tableau contenu dans l'archive",
                    members,
                    key=f"nasa_member_{study_id}_{index}",
                )
                preview_key = f"nasa_preview_{study_id}_{index}"
            else:
                member = None
                preview_key = None
        elif filename.endswith((".csv", ".tsv", ".txt")):
            member = None
            preview_key = f"nasa_preview_{study_id}_{index}"
        else:
            member = None
            preview_key = None

        if preview_key and st.button("Aperçu du tableau", key=preview_key):
            try:
                with st.spinner("Téléchargement et lecture du fichier NASA..."):
                    frame, source_name = _preview(item, member)
                st.caption(f"Source : OSD-{study_id} · {source_name} · aperçu des 100 premières lignes")
                st.dataframe(frame.head(100), width="stretch", hide_index=True)
                st.caption(
                    "Les colonnes et unités sont celles du fichier source. "
                    "Aucune conversion vers les indicateurs cliniques BioSpace n'est effectuée."
                )
            except nasa_osdr.OSDRError as exc:
                st.warning(str(exc))
        if item.get("description"):
            st.caption(item["description"])


def _render_physiology():
    st.markdown("#### Physiologie et comportement des astronautes")
    st.write(
        "La NASA Spaceflight Standard Measures collecte notamment l'activité et l'exposition "
        "à la lumière par actigraphie, le sommeil, la cognition, les fonctions sensorimotrices, "
        "la force musculaire, des marqueurs biologiques et des mesures cardiovasculaires."
    )
    st.markdown("[Consulter la description officielle NASA — Standard Measures](https://www.nasa.gov/reference/standard-measures/)")
    st.markdown("[Ouvrir le NASA Life Sciences Portal (NLSP)](https://nlsp.nasa.gov/)")
    st.markdown("[Documentation NASA sur le programme Standard Measures](https://ntrs.nasa.gov/citations/20230014025)")
    st.info(
        "Les données détaillées du programme Standard Measures sont archivées dans le NASA Life "
        "Sciences Data Archive. Certaines données individuelles ou détaillées peuvent nécessiter "
        "une demande et une approbation. BioSpace ne contourne pas ces contrôles."
    )
    st.warning(
        "À ce stade, aucun fichier physiologique individuel n'est présenté comme déjà importé. "
        "Nous devons d'abord identifier les fichiers publics et/ou obtenir l'autorisation officielle "
        "pour les données restreintes."
    )
    st.markdown("**Variables à rechercher dans les fichiers autorisés :**")
    st.markdown(
        "- Actigraphie : activité, lumière, rythmes veille-sommeil.\n"
        "- Sommeil : durée et qualité, selon le protocole et les champs réellement fournis.\n"
        "- Sensorimoteur : équilibre, coordination et résultats de tests fonctionnels.\n"
        "- Cardiovasculaire : mesures structurelles ou réponses orthostatiques disponibles.\n"
        "- Muscle : tests de force et de performance."
    )


def render(ctx=None):
    st.markdown("### Données de recherche spatiale — sources NASA")
    st.caption(
        "Connexion facultative au catalogue public NASA OSDR. Les autres fonctions de BioSpace "
        "restent utilisables hors ligne. Les fichiers NASA sont consultés séparément des profils "
        "de démonstration et des mesures quotidiennes saisies."
    )
    biology, physiology = st.tabs(["Biologie et biomarqueurs", "Physiologie et comportement"])
    with biology:
        _render_biology()
    with physiology:
        _render_physiology()
