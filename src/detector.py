"""Détecte les écarts par rapport à la baseline personnelle.

Méthode : z-score de la moyenne glissante de chaque indicateur par rapport
à la baseline de l'astronaute, orienté selon le sens dangereux de l'écart,
agrégé par système physiologique (pire indicateur du domaine). Des seuils
critiques absolus déclenchent l'état rouge sans attendre.

Le DataFrame d'entrée contient une ligne par jour calendaire (voir
`storage.load_frame`), avec des NaN pour les mesures manquantes.
"""
import numpy as np
import pandas as pd

from src.config import CRITICAL, DIRECTION, DOMAIN_ORDER, DOMAINS, MIN_STD

BASELINE_DAYS = 30    # période de référence (jours "normaux")
BASELINE_MIN_OBS = 15  # mesures minimales dans la référence pour un indicateur
WINDOW = 7            # lissage sur 7 jours pour ignorer le bruit d'un seul jour
MIN_PERIODS = 4       # mesures minimales dans la fenêtre glissante
ORANGE, RED = 2.5, 4.0
PERSISTENCE = 3       # un écart doit durer 3 jours consécutifs pour déclencher un état
CRITICAL_LOOKBACK = 3  # un seuil critique est vérifié sur les 3 derniers jours


def calibration_progress(df):
    """Fraction (0 à 1) de la période de référence déjà couverte."""
    return min(len(df), BASELINE_DAYS) / BASELINE_DAYS


def compute_zscores(df):
    """Z-score de la moyenne glissante de chaque indicateur vs la baseline.

    Pendant la calibration (moins de BASELINE_DAYS jours), tous les z-scores
    valent NaN : aucun état n'est calculé.
    """
    cols = list(DOMAINS)
    if len(df) < BASELINE_DAYS:
        z = pd.DataFrame(np.nan, index=df.index, columns=cols)
        z.insert(0, "date", df["date"])
        return z

    baseline = df.iloc[:BASELINE_DAYS][cols]
    n_base = baseline.count()
    mean = baseline.mean()
    # Plancher d'écart-type : une baseline constante ne doit ni désactiver l'indicateur
    # (division par zéro) ni rendre le moindre écart démesuré. NaN (< 2 mesures) reste NaN.
    std = np.maximum(baseline.std(), pd.Series(MIN_STD).reindex(baseline.columns))
    insufficient = n_base < BASELINE_MIN_OBS
    mean[insufficient] = np.nan

    roll = df[cols].rolling(WINDOW, min_periods=MIN_PERIODS)
    rolling, n_roll = roll.mean(), roll.count()
    # Erreur de prédiction : bruit de la moyenne sur n jours + incertitude
    # de la baseline estimée sur n_base jours.
    scale = std * np.sqrt(1 / n_roll.replace(0, np.nan) + 1 / n_base.replace(0, np.nan))
    z = (rolling - mean) / scale
    z.insert(0, "date", df["date"])
    return z


def danger_score(z, direction):
    """Transforme le z-score signé en score de danger (positif = mauvais)."""
    if direction == "up":
        return z
    if direction == "down":
        return -z
    return abs(z)


def to_status(score):
    """Convertit un score de danger en vert / orange / rouge."""
    if pd.isna(score):
        return "inconnu"
    if score >= RED:
        return "rouge"
    if score >= ORANGE:
        return "orange"
    return "vert"


def indicator_scores(z_df):
    """Score de danger persistant de chaque indicateur (NaN si inconnu).

    On retient le plus faible des PERSISTENCE derniers jours : seul un écart
    qui dure déclenche une alerte, un pic isolé de bruit est ignoré.
    """
    tail = z_df.iloc[-PERSISTENCE:]
    return {c: danger_score(tail[c], DIRECTION[c]).min(skipna=False) for c in DOMAINS}


def green_streaks(z_df):
    """Nombre de jours consécutifs (jusqu'au dernier) où chaque domaine est sous le seuil orange.

    Calculé sur les données elles-mêmes : indépendant de la fréquence des consultations.
    Un jour sans score calculable interrompt la série.
    """
    if len(z_df) == 0:
        return {d: 0 for d in DOMAIN_ORDER}
    scores = domain_score_series(z_df)
    out = {}
    for domain in DOMAIN_ORDER:
        ok = (scores[domain] < ORANGE).to_numpy()[::-1]
        n = 0
        for flag in ok:
            if not flag:
                break
            n += 1
        out[domain] = n
    return out


def domain_details(z_df):
    """Pour chaque domaine : score (pire indicateur), état et indicateur responsable.

    Retourne {domaine: {"score", "status", "driver", "drivers", "critical"}} où
    `drivers` liste les indicateurs du domaine triés du plus au moins préoccupant.
    """
    per_indicator = indicator_scores(z_df)
    streaks = green_streaks(z_df)
    details = {}
    for domain in DOMAIN_ORDER:
        members = [c for c in DOMAINS if DOMAINS[c] == domain]
        valid = {c: per_indicator[c] for c in members if not pd.isna(per_indicator[c])}
        if not valid:
            details[domain] = {"score": float("nan"), "status": "inconnu",
                               "driver": None, "drivers": [], "critical": [],
                               "green_streak": 0}
            continue
        ranked = sorted(valid, key=valid.get, reverse=True)
        worst = valid[ranked[0]]
        details[domain] = {
            "score": worst,
            "status": to_status(worst),
            "driver": ranked[0],
            "drivers": [(c, valid[c]) for c in ranked],
            "critical": [],
            "green_streak": streaks[domain],
        }
    return details


def domain_score_series(z_df):
    """Score de danger persistant de chaque domaine, pour chaque jour (vectorisé).

    Équivalent de `domain_details` appliqué à chaque jour, mais calculé en une passe :
    sert à la validation sur de nombreuses simulations. Colonnes : un domaine chacune.
    """
    danger = pd.DataFrame({c: danger_score(z_df[c], DIRECTION[c]) for c in DOMAINS})
    persistent = danger.rolling(PERSISTENCE).min()
    out = {}
    for domain in DOMAIN_ORDER:
        members = [c for c in DOMAINS if DOMAINS[c] == domain]
        out[domain] = persistent[members].max(axis=1, skipna=True)
    return pd.DataFrame(out)


def critical_hits(df):
    """Indicateurs dont une valeur récente dépasse un seuil critique absolu.

    Retourne une liste de dict(indicator, value, limit, date).
    """
    hits = []
    tail = df.iloc[-CRITICAL_LOOKBACK:]
    for c, (low, high) in CRITICAL.items():
        series = tail[c].dropna()
        if series.empty:
            continue
        for date, value in zip(tail.loc[series.index, "date"], series):
            if low is not None and value < low:
                hits.append({"indicator": c, "value": float(value), "limit": low, "date": date})
            elif high is not None and value > high:
                hits.append({"indicator": c, "value": float(value), "limit": high, "date": date})
    return hits


def evaluate(df):
    """Évaluation complète : (z-scores, détails par domaine).

    Un seuil critique force l'état rouge du domaine, quelle que soit la baseline,
    sans attendre la persistance. Fonctionne aussi pendant la calibration.
    """
    z = compute_zscores(df)
    details = domain_details(z)
    for hit in critical_hits(df) if len(df) else []:
        d = details[DOMAINS[hit["indicator"]]]
        d["critical"].append(hit)
        d["status"] = "rouge"
        d["green_streak"] = 0
        d["score"] = RED if pd.isna(d["score"]) else max(d["score"], RED)
        if d["driver"] is None or all(c != hit["indicator"] for c, _ in d["drivers"]):
            d["drivers"].insert(0, (hit["indicator"], RED))
            d["driver"] = hit["indicator"]
    return z, details


def current_status(z_df):
    """État de chaque domaine au dernier jour (statistique, sans seuils critiques)."""
    return {d: v["status"] for d, v in domain_details(z_df).items()}

def current_scores(z_df):
    """Score de danger de chaque domaine au dernier jour (0 = normal)."""
    last = z_df.iloc[-1]
    scores = {DOMAINS[c]: danger_score(last[c], DIRECTION[c]) for c in DOMAINS}
    return {d: 0.0 if pd.isna(s) else max(0.0, s) for d, s in scores.items()}

if __name__ == "__main__":
    # Utilise le générateur commun : l'exécution du détecteur ne dépend
    # plus de fichiers CSV présents ou manquants dans data/.
    from src.config import SCENARIO_NAMES
    from src.generator import generate_demo

    for scenario in SCENARIO_NAMES:
        df = generate_demo(scenario)
        print(f"\n--- {scenario} ---")
        for domain, v in evaluate(df)[1].items():
            print(f"{domain:20s} {v['status']}")
