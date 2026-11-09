"""Validation du détecteur sur de nombreuses simulations.

Mesure deux choses, sur des graines aléatoires distinctes :
  - le taux de fausses alertes sur des missions nominales ;
  - le taux et le délai de détection de chaque scénario.

Les seuils critiques absolus ne sont pas inclus (ils ne dépendent pas de la baseline).
"""
import numpy as np
import pandas as pd

from src.config import SCENARIO_NAMES
from src.detector import BASELINE_DAYS, ORANGE, RED, compute_zscores, domain_score_series
from src.generator import generate

# scénario -> (domaine concerné, jour de début de l'anomalie simulée)
EXPECTED = {
    "sleep_stress": ("Comportement", 30),
    "solar_event": ("Radiation", 100),
    "deconditioning": ("Os et muscles", 30),
    "sans_risk": ("Neuro-oculaire", 40),
    "isolation": ("Comportement", 30),
    "infection": ("Sang et immunité", 118),
    "cardio_event": ("Cardiovasculaire", 60),
}


def false_alarm_stats(n_seeds=40, missing_rate=0.0):
    """Part des jours (après calibration) où au moins un domaine est orange/rouge."""
    orange_days = red_days = total = 0
    for seed in range(n_seeds):
        df = generate(scenario="normal", seed=1000 + seed, missing_rate=missing_rate)
        scores = domain_score_series(compute_zscores(df)).iloc[BASELINE_DAYS + 6:]
        worst = scores.max(axis=1, skipna=True)
        orange_days += int((worst >= ORANGE).sum())
        red_days += int((worst >= RED).sum())
        total += len(worst)
    return {"alert_days_pct": 100 * orange_days / total, "red_days_pct": 100 * red_days / total,
            "days": total, "seeds": n_seeds, "missing_rate": missing_rate}


def detection_stats(scenario, n_seeds=40, missing_rate=0.0):
    """Taux de détection et délai (jours après le début de l'anomalie) d'un scénario."""
    domain, onset = EXPECTED[scenario]
    delays = []
    for seed in range(n_seeds):
        df = generate(scenario=scenario, seed=1000 + seed, missing_rate=missing_rate)
        scores = domain_score_series(compute_zscores(df))[domain]
        after = scores.iloc[onset:]
        hit = after[after >= ORANGE]
        if len(hit):
            delays.append(int(hit.index[0] - onset))
    rate = len(delays) / n_seeds
    return {
        "scenario": scenario, "name": SCENARIO_NAMES[scenario], "domain": domain,
        "detected_pct": 100 * rate,
        "median_delay": float(np.median(delays)) if delays else None,
        "p90_delay": float(np.percentile(delays, 90)) if delays else None,
        "seeds": n_seeds,
    }


def full_validation(n_seeds=40, missing_rate=0.0):
    return {
        "false_alarms": false_alarm_stats(n_seeds, missing_rate),
        "detection": [detection_stats(s, n_seeds, missing_rate) for s in EXPECTED],
    }


def as_table(result):
    return pd.DataFrame(result["detection"]).rename(columns={
        "name": "Scénario", "domain": "Système", "detected_pct": "Détection (%)",
        "median_delay": "Délai médian (j)", "p90_delay": "Délai 90 % (j)"})[
        ["Scénario", "Système", "Détection (%)", "Délai médian (j)", "Délai 90 % (j)"]]
