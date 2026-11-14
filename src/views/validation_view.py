"""Page de validation : fausses alertes et délais de détection mesurés."""
import plotly.graph_objects as go
import streamlit as st

from src import validation


@st.cache_data(show_spinner=False)
def _run(n_seeds, missing_rate):
    return validation.full_validation(n_seeds, missing_rate)


def render(ctx):
    st.markdown("##### Validation du détecteur")
    st.caption("Le détecteur est testé sur des centaines de missions simulées avec des graines "
               "aléatoires distinctes de celles de la démonstration. Résultats mesurés ici, "
               "pas déclarés.")
    c1, c2 = st.columns(2)
    n_seeds = c1.select_slider("Missions simulées par scénario", [10, 20, 40, 80], value=40)
    missing = c2.select_slider("Mesures manquantes", [0.0, 0.1, 0.2], value=0.0,
                               format_func=lambda x: f"{int(x * 100)} %")
    # Streamlit exécute tous les onglets à chaque clic : on ne lance la simulation (plusieurs
    # secondes) que sur demande, puis le résultat reste en cache.
    if not st.session_state.get("validation_started"):
        if st.button("Lancer la validation", type="primary", key="validation_start"):
            st.session_state["validation_started"] = True
            st.rerun()
        st.info("La simulation prend quelques secondes ; elle n'est lancée que sur demande.")
        return
    with st.spinner("Simulation en cours..."):
        res = _run(n_seeds, missing)

    fa = res["false_alarms"]
    k1, k2, k3 = st.columns(3)
    k1.metric("Jours avec une alerte (mission nominale)", f"{fa['alert_days_pct']:.1f} %")
    k2.metric("Jours en rouge (mission nominale)", f"{fa['red_days_pct']:.2f} %")
    detected = [d["detected_pct"] for d in res["detection"]]
    k3.metric("Scénarios détectés", f"{sum(detected) / len(detected):.0f} %")
    st.caption(f"Fausses alertes : {fa['days']} jours simulés sans anomalie, tous systèmes confondus "
               f"({len(res['detection'])} scénarios d'anomalie testés ci-dessous).")

    table = validation.as_table(res)
    st.dataframe(table, hide_index=True, width="stretch")

    fig = go.Figure(go.Bar(
        x=[d["name"] for d in res["detection"]],
        y=[d["median_delay"] or 0 for d in res["detection"]],
        error_y=dict(type="data", symmetric=False, array=[
            max(0, (d["p90_delay"] or 0) - (d["median_delay"] or 0)) for d in res["detection"]],
            arrayminus=[0] * len(res["detection"])),
        marker_color="#4F8BF9"))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", height=340, yaxis_title="Jours après le début",
                      margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Délai = jours entre le début de l'anomalie simulée et la première alerte du système "
               "concerné (barre : médiane, trait : 90e centile). Les dérives simulées sont lentes : "
               "elles s'étalent sur 150 jours, donc un délai de 30 jours correspond à un écart encore faible. "
               "Les seuils critiques absolus ne sont pas inclus dans ces mesures.")
