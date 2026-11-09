"""Calculs de synthèse partagés par l'interface et les rapports."""
import pandas as pd

from src.config import DECIMALS, DOMAIN_ORDER, DOMAINS, LABELS, UNITS
from src.detector import BASELINE_DAYS, WINDOW, indicator_scores, to_status


def fmt(value, indicator):
    if pd.isna(value):
        return "n/d"
    return f"{value:.{DECIMALS[indicator]}f}"


def with_unit(value, indicator):
    """Valeur formatée suivie de son unité ("5.8/10", "66 bpm")."""
    unit = UNITS[indicator]
    text = fmt(value, indicator)
    if not unit or text == "n/d":
        return text
    return f"{text}{'' if unit.startswith('/') else ' '}{unit}"


def recent_and_reference(df):
    """(moyenne des WINDOW derniers jours, référence personnelle) par indicateur."""
    cols = list(DOMAINS)
    recent = df[cols].tail(WINDOW).mean()
    reference = df.iloc[:BASELINE_DAYS][cols].mean() if len(df) >= BASELINE_DAYS else recent * float("nan")
    return recent, reference


def indicator_rows(df, z):
    """Une ligne par indicateur : valeur récente, référence, écart relatif, état."""
    recent, reference = recent_and_reference(df)
    scores = indicator_scores(z)
    rows = []
    for c in DOMAINS:
        ref, cur = reference[c], recent[c]
        delta = None if pd.isna(ref) or pd.isna(cur) or ref == 0 else (cur - ref) / abs(ref) * 100
        rows.append({
            "indicator": c, "domain": DOMAINS[c], "label": LABELS[c], "unit": UNITS[c],
            "value": cur, "reference": ref, "delta_pct": delta,
            "score": scores[c], "status": to_status(scores[c]),
        })
    return rows


def domain_rows(details):
    """Résumé par domaine, dans l'ordre d'affichage."""
    out = []
    for domain in DOMAIN_ORDER:
        d = details[domain]
        out.append({"domain": domain, "status": d["status"], "score": d["score"],
                    "driver": d["driver"], "critical": d["critical"]})
    return out


def mission_summary(details):
    statuses = [d["status"] for d in details.values()]
    return {
        "rouge": statuses.count("rouge"),
        "orange": statuses.count("orange"),
        "vert": statuses.count("vert"),
        "inconnu": statuses.count("inconnu"),
    }
