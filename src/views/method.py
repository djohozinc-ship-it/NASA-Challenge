"""Onglet Méthode : principe, paramètres et limites."""
import streamlit as st

from src.config import ESCALATION_DAYS, RESOLVE_DAYS
from src.detector import BASELINE_DAYS, ORANGE, PERSISTENCE, RED, WINDOW


def render(ctx):
    st.markdown(f"""
**Principe.** Chaque astronaute est comparé à *sa propre* normale, pas à une norme générale.
Le calcul est entièrement local : aucune connexion au réseau terrestre n'est nécessaire.

1. **Calibration** : les {BASELINE_DAYS} premiers jours définissent la référence personnelle
   (moyenne et écart-type de chaque indicateur). Pendant cette période, seuls les seuils critiques sont actifs.
2. **Lissage** : moyenne glissante sur {WINDOW} jours pour ignorer le bruit quotidien. Les mesures manquantes sont tolérées.
3. **Écart** : z-score de la moyenne glissante, normalisé par le bruit de la moyenne et par
   l'incertitude de la référence, orienté selon le sens dangereux de chaque indicateur.
4. **Persistance** : l'écart doit durer {PERSISTENCE} jours consécutifs pour compter.
5. **Système physiologique** : son état est celui de son indicateur le plus préoccupant.
   Orange à partir de {ORANGE}, rouge à partir de {RED}.
6. **Seuils critiques absolus** : une valeur du jour hors d'une borne de sécurité (tension, température,
   fréquence cardiaque, hémoglobine, acuité visuelle, sommeil, débit de dose) passe le système en rouge
   immédiatement, sans attendre la persistance ni la fin de la calibration.

**Suivi des actions.** Chaque alerte est suivie : à faire, fait, reporté, signalé à l'équipe médicale.
Sans action, elle est escaladée automatiquement après {ESCALATION_DAYS['rouge']} jour (rouge) ou
{ESCALATION_DAYS['orange']} jours (orange). Une alerte est close après {RESOLVE_DAYS} jours consécutifs
au vert, pour éviter le clignotement.

**Validation.** Voir l'onglet *Validation* : taux de fausses alertes et délais de détection mesurés
sur de nombreuses missions simulées.

**Limites.** Données synthétiques ou auto-déclarées, seuils illustratifs non validés cliniquement,
référence fixe de {BASELINE_DAYS} jours, conseils généraux non médicaux. Ne remplace pas un avis médical.
""")
