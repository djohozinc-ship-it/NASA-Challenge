"""Configuration centrale : indicateurs, domaines, unités, sens du danger.

Un seul endroit à modifier pour ajouter un indicateur au système.
"""

# Ordre d'affichage des domaines (système physiologique évalué)
DOMAIN_ORDER = [
    "Cardiovasculaire",
    "Os et muscles",
    "Neuro-oculaire",
    "Colonne vertébrale",
    "Sang et immunité",
    "Radiation",
    "Comportement",
]

# indicateur -> métadonnées
#   domain    : système physiologique auquel il contribue
#   direction : sens dangereux d'un écart ("up", "down" ou "both")
#   label/unit: affichage
#   decimals  : précision d'affichage
#   valid     : (min, max) plausibles ; toute saisie hors bornes est rejetée
#   critical  : (bas, haut) seuils absolus ; une valeur du jour hors de cet
#               intervalle déclenche immédiatement l'état rouge (None = pas de borne)
#   source    : "auto" (capteur) ou "saisie" (bilan quotidien de l'astronaute)
INDICATORS = {
    "resting_hr":    {"domain": "Cardiovasculaire",   "direction": "both", "label": "Fréquence cardiaque au repos", "unit": "bpm",   "decimals": 0, "valid": (20, 250),  "critical": (40, 130),   "source": "auto"},
    "hrv":           {"domain": "Cardiovasculaire",   "direction": "down", "label": "Variabilité cardiaque (RMSSD)", "unit": "ms",    "decimals": 0, "valid": (1, 300),   "critical": None,        "source": "auto"},
    "bp_systolic":   {"domain": "Cardiovasculaire",   "direction": "both", "label": "Tension systolique",           "unit": "mmHg",  "decimals": 0, "valid": (50, 260),  "critical": (80, 160),   "source": "auto"},
    "exercise_min":  {"domain": "Os et muscles",      "direction": "down", "label": "Activité physique",             "unit": "min/j", "decimals": 0, "valid": (0, 600),   "critical": None,        "source": "auto"},
    "weight":        {"domain": "Os et muscles",      "direction": "down", "label": "Poids",                         "unit": "kg",    "decimals": 1, "valid": (20, 250),  "critical": None,        "source": "auto"},
    "visual_acuity": {"domain": "Neuro-oculaire",     "direction": "down", "label": "Acuité visuelle",               "unit": "",      "decimals": 2, "valid": (0, 2.0),   "critical": (0.6, None), "source": "saisie"},
    "back_pain":     {"domain": "Colonne vertébrale", "direction": "up",   "label": "Douleur dorsale",               "unit": "/10",   "decimals": 1, "valid": (0, 10),    "critical": None,        "source": "saisie"},
    "fatigue":       {"domain": "Sang et immunité",   "direction": "up",   "label": "Indice de fatigue",             "unit": "/10",   "decimals": 1, "valid": (0, 10),    "critical": None,        "source": "saisie"},
    "hemoglobin":    {"domain": "Sang et immunité",   "direction": "down", "label": "Hémoglobine (proxy globules rouges)", "unit": "g/dL", "decimals": 1, "valid": (3, 22), "critical": (10, None), "source": "auto"},
    "temperature":   {"domain": "Sang et immunité",   "direction": "up",   "label": "Température corporelle",        "unit": "°C",    "decimals": 1, "valid": (30, 43),   "critical": (None, 38.5), "source": "auto"},
    "symptoms":      {"domain": "Sang et immunité",   "direction": "up",   "label": "Symptômes (gorge, peau, fièvre)", "unit": "/10", "decimals": 1, "valid": (0, 10),    "critical": None,        "source": "saisie"},
    "dose_rate":     {"domain": "Radiation",          "direction": "up",   "label": "Débit de dose",                 "unit": "mSv/j", "decimals": 2, "valid": (0, 100),   "critical": (None, 5.0), "source": "auto"},
    "sleep_hours":   {"domain": "Comportement",       "direction": "down", "label": "Sommeil",                       "unit": "h",     "decimals": 1, "valid": (0, 24),    "critical": (3, None),   "source": "auto"},
    "mood":          {"domain": "Comportement",       "direction": "down", "label": "Humeur (questionnaire)",        "unit": "/10",   "decimals": 1, "valid": (0, 10),    "critical": None,        "source": "saisie"},
    "stress":        {"domain": "Comportement",       "direction": "up",   "label": "Stress quotidien",              "unit": "/10",   "decimals": 1, "valid": (0, 10),    "critical": None,        "source": "saisie"},
    "social":        {"domain": "Comportement",       "direction": "down", "label": "Contacts sociaux",              "unit": "/10",   "decimals": 1, "valid": (0, 10),    "critical": None,        "source": "saisie"},
}

# Écart-type minimal retenu pour la baseline de chaque indicateur (même unité que l'indicateur).
# Sans plancher, une référence très régulière (douleur toujours à 0, poids constant) donne un
# écart-type nul ou minuscule : soit l'indicateur n'est jamais évalué, soit le moindre écart
# produit un z-score démesuré. Ces valeurs correspondent à la résolution réaliste de la mesure.
MIN_STD = {
    "resting_hr": 1.5, "hrv": 2.5, "bp_systolic": 2.5, "exercise_min": 10.0, "weight": 0.15,
    "visual_acuity": 0.02, "back_pain": 0.7, "fatigue": 0.7, "hemoglobin": 0.15,
    "temperature": 0.1, "symptoms": 0.7, "dose_rate": 0.02, "sleep_hours": 0.3,
    "mood": 0.7, "stress": 0.7, "social": 0.7,   # échelles /10 : ~1 point d'auto-évaluation
}
assert set(MIN_STD) == set(INDICATORS), "MIN_STD doit couvrir exactement les indicateurs"

DOMAINS = {k: v["domain"] for k, v in INDICATORS.items()}
DIRECTION = {k: v["direction"] for k, v in INDICATORS.items()}
LABELS = {k: v["label"] for k, v in INDICATORS.items()}
UNITS = {k: v["unit"] for k, v in INDICATORS.items()}
DECIMALS = {k: v["decimals"] for k, v in INDICATORS.items()}
VALID = {k: v["valid"] for k, v in INDICATORS.items()}
CRITICAL = {k: v["critical"] for k, v in INDICATORS.items() if v["critical"]}

SCENARIO_NAMES = {
    "normal": "Mission nominale",
    "sleep_stress": "Dégradation sommeil et stress",
    "solar_event": "Éruption solaire",
    "deconditioning": "Déconditionnement musculo-squelettique",
    "sans_risk": "Risque neuro-oculaire (SANS)",
    "isolation": "Isolement et confinement",
    "infection": "Épisode infectieux",
    "cardio_event": "Dérive cardiovasculaire",
}

# Jour d'ouverture suggéré par scénario (là où l'événement est visible)
SCENARIO_FOCUS = {"solar_event": 104, "infection": 125}

# Escalade automatique : jours sans action avant remontée à l'équipe médicale
ESCALATION_DAYS = {"rouge": 1, "orange": 3}

# Hystérésis : jours consécutifs au vert avant de clore une alerte (évite le clignotement)
RESOLVE_DAYS = 3
