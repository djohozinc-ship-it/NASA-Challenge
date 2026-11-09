"""Génère des données de santé synthétiques pour un astronaute."""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42

# Pour chaque indicateur : valeur normale, bruit quotidien, bornes réalistes
INDICATORS = {
    "resting_hr":    {"base": 60,   "noise": 3,    "low": 40,  "high": 140},
    "hrv":           {"base": 50,   "noise": 5,    "low": 10,  "high": 100},
    "bp_systolic":   {"base": 118,  "noise": 5,    "low": 80,  "high": 220},
    "exercise_min":  {"base": 120,  "noise": 20,   "low": 0,   "high": 240},
    "weight":        {"base": 75,   "noise": 0.3,  "low": 40,  "high": 120},
    "visual_acuity": {"base": 1.0,  "noise": 0.03, "low": 0.1, "high": 1.5},
    "back_pain":     {"base": 2,    "noise": 0.8,  "low": 0,   "high": 10},
    "fatigue":       {"base": 3,    "noise": 1.0,  "low": 0,   "high": 10},
    "hemoglobin":    {"base": 15,   "noise": 0.3,  "low": 5,   "high": 20},
    "temperature":   {"base": 36.7, "noise": 0.2,  "low": 34,  "high": 41},
    "symptoms":      {"base": 1,    "noise": 0.7,  "low": 0,   "high": 10},
    "dose_rate":     {"base": 0.5,  "noise": 0.05, "low": 0,   "high": None},
    "sleep_hours":   {"base": 7,    "noise": 0.6,  "low": 0,   "high": 12},
    "mood":          {"base": 7,    "noise": 0.8,  "low": 0,   "high": 10},
    "stress":        {"base": 3,    "noise": 0.8,  "low": 0,   "high": 10},
    "social":        {"base": 6,    "noise": 1.0,  "low": 0,   "high": 10},
}

# drifts : indicateur -> (jour de début, changement total à la fin)
# spikes : indicateur -> (jour de début, durée en jours, ajout par jour)
SCENARIOS = {
    "normal": {"drifts": {}, "spikes": {}},
    "sleep_stress": {
        "drifts": {
            "sleep_hours": (30, -2.0),
            "fatigue": (30, +3.0),
            "resting_hr": (40, +6.0),
            "stress": (30, +3.0),
            "mood": (35, -2.5),
            "hrv": (40, -12.0),
        },
        "spikes": {},
    },
    "solar_event": {"drifts": {}, "spikes": {"dose_rate": (100, 3, 1.0)}},
    # Perte d'exercice, de masse et de qualité osseuse/musculaire, douleur dorsale
    "deconditioning": {
        "drifts": {
            "exercise_min": (30, -80.0),
            "weight": (35, -4.0),
            "back_pain": (40, +3.5),
            "hrv": (45, -8.0),
        },
        "spikes": {},
    },
    # Syndrome neuro-oculaire associé aux vols spatiaux, plus anémie spatiale
    "sans_risk": {
        "drifts": {
            "visual_acuity": (40, -0.25),
            "hemoglobin": (35, -2.5),
            "fatigue": (50, +2.5),
        },
        "spikes": {},
    },
    # Isolement et confinement : retrait social, humeur, sommeil
    "isolation": {
        "drifts": {
            "social": (30, -4.0),
            "mood": (35, -3.0),
            "sleep_hours": (40, -1.5),
            "stress": (40, +2.5),
        },
        "spikes": {},
    },
    # Épisode infectieux de 6 jours : fièvre, symptômes, fatigue
    "infection": {
        "drifts": {},
        "spikes": {
            "temperature": (120, 6, 0.9),
            "symptoms": (118, 8, 3.5),
            "fatigue": (120, 6, 2.0),
        },
    },
    # Dérive cardiovasculaire lente, jusqu'au seuil critique de tension
    "cardio_event": {
        "drifts": {
            "bp_systolic": (60, +48.0),
            "resting_hr": (60, +14.0),
            "hrv": (60, -16.0),
        },
        "spikes": {},
    },
}


# Graines retenues pour la démonstration : sans bruit parasite hors de l'événement simulé.
# Les performances globales (fausses alertes, délais) sont mesurées sur de nombreuses
# graines dans src/validation.py, pas sur ce choix.
DEMO_SEEDS = {
    "normal": 25, "sleep_stress": 0, "solar_event": 25, "deconditioning": 0,
    "sans_risk": 25, "isolation": 25, "infection": 25, "cardio_event": 0,
}


def generate_demo(scenario, n_days=180):
    """Série de démonstration d'un scénario (graine fixe)."""
    return generate(n_days=n_days, scenario=scenario, seed=DEMO_SEEDS[scenario])


def generate(n_days=180, scenario="normal", seed=SEED, missing_rate=0.0):
    """Retourne un DataFrame : une ligne par jour, une colonne par indicateur.

    missing_rate : proportion de mesures manquantes (oublis de saisie, panne de capteur).
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2026-01-01", periods=n_days, freq="D")
    data = {"date": dates}
    drifts = SCENARIOS[scenario]["drifts"]
    spikes = SCENARIOS[scenario]["spikes"]

    for name, p in INDICATORS.items():
        values = p["base"] + rng.normal(0, p["noise"], n_days)

        if name in drifts:
            start, change = drifts[name]
            ramp = np.clip((np.arange(n_days) - start) / (n_days - start), 0, 1)
            values = values + ramp * change

        if name in spikes:
            start, duration, extra = spikes[name]
            values[start:start + duration] += extra

        data[name] = np.clip(values, p["low"], p["high"])

    df = pd.DataFrame(data)
    if missing_rate > 0:
        mask_rng = np.random.default_rng(seed + 1)
        for name in INDICATORS:
            df.loc[mask_rng.random(n_days) < missing_rate, name] = np.nan
    df["dose_cumulative"] = df["dose_rate"].fillna(0).cumsum()
    return df


if __name__ == "__main__":
    out_dir = Path(__file__).parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    for scenario in SCENARIOS:
        generate_demo(scenario).to_csv(out_dir / f"{scenario}.csv", index=False)
        print(f"{scenario}.csv créé")
