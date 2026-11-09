"""Tests du générateur, du détecteur et de la cohérence de la configuration."""
import numpy as np
import pandas as pd
import pytest

from src.actions import ACTIONS, build_cards
from src.config import DOMAIN_ORDER, DOMAINS, INDICATORS, SCENARIO_FOCUS, SCENARIO_NAMES
from src.detector import (
    BASELINE_DAYS, calibration_progress, compute_zscores, current_status, domain_details,
    domain_score_series, evaluate,
)
from src.generator import INDICATORS as GEN_INDICATORS
from src.generator import SCENARIOS, generate, generate_demo


def status_at(scenario, day=180):
    df = generate_demo(scenario).iloc[:day]
    return current_status(compute_zscores(df))


def test_config_is_consistent():
    assert set(GEN_INDICATORS) == set(INDICATORS)
    assert set(SCENARIOS) == set(SCENARIO_NAMES)
    assert set(DOMAINS.values()) == set(DOMAIN_ORDER)
    assert set(ACTIONS) == set(DOMAIN_ORDER)


def test_nominal_mission_is_all_green():
    assert set(status_at("normal").values()) == {"vert"}


@pytest.mark.parametrize("scenario, day, domain", [
    ("sleep_stress", 180, "Comportement"),
    ("sleep_stress", 180, "Cardiovasculaire"),
    ("solar_event", SCENARIO_FOCUS["solar_event"], "Radiation"),
    ("deconditioning", 180, "Os et muscles"),
    ("deconditioning", 180, "Colonne vertébrale"),
    ("sans_risk", 180, "Neuro-oculaire"),
    ("sans_risk", 180, "Sang et immunité"),
    ("isolation", 180, "Comportement"),
    ("infection", SCENARIO_FOCUS["infection"], "Sang et immunité"),
    ("cardio_event", 180, "Cardiovasculaire"),
])
def test_scenarios_raise_expected_alert(scenario, day, domain):
    assert status_at(scenario, day)[domain] == "rouge"


def test_isolated_spike_is_ignored():
    """Un seul jour aberrant ne doit pas déclencher d'alerte (persistance)."""
    df = generate(scenario="normal", seed=25)
    df.loc[150, "resting_hr"] = 115
    status = current_status(compute_zscores(df.iloc[:151]))
    assert status["Cardiovasculaire"] == "vert"


def test_domain_status_is_worst_indicator():
    df = generate_demo("sleep_stress")
    details = domain_details(compute_zscores(df))
    behaviour = details["Comportement"]
    assert behaviour["score"] == max(s for _, s in behaviour["drivers"])
    assert behaviour["driver"] == behaviour["drivers"][0][0]


def test_constant_baseline_does_not_crash():
    df = generate(scenario="normal")
    df.loc[:BASELINE_DAYS - 1, "weight"] = 75.0   # écart-type nul
    assert set(current_status(compute_zscores(df))) == set(DOMAIN_ORDER)


def test_calibration_has_no_statistical_status():
    df = generate_demo("sleep_stress").iloc[:20]
    z, details = evaluate(df)
    assert calibration_progress(df) == pytest.approx(20 / BASELINE_DAYS)
    assert {d["status"] for d in details.values()} == {"inconnu"}


def test_critical_threshold_triggers_red_immediately_even_in_calibration():
    df = generate_demo("normal").iloc[:10].copy()
    df.loc[9, "bp_systolic"] = 175
    _, details = evaluate(df)
    assert details["Cardiovasculaire"]["status"] == "rouge"
    assert details["Cardiovasculaire"]["critical"][0]["indicator"] == "bp_systolic"


def test_critical_low_threshold():
    df = generate_demo("normal").iloc[:60].copy()
    df.loc[59, "hemoglobin"] = 8.5
    assert evaluate(df)[1]["Sang et immunité"]["status"] == "rouge"


def test_cardio_scenario_ends_on_critical_blood_pressure():
    _, details = evaluate(generate_demo("cardio_event"))
    assert any(h["indicator"] == "bp_systolic" for h in details["Cardiovasculaire"]["critical"])


def test_missing_data_is_tolerated():
    df = generate(scenario="normal", seed=25, missing_rate=0.2)
    status = current_status(compute_zscores(df))
    assert set(status) == set(DOMAIN_ORDER)
    assert "rouge" not in status.values()


def test_vectorised_series_matches_per_day_evaluation():
    z = compute_zscores(generate(scenario="sleep_stress", seed=3))
    series = domain_score_series(z)
    for day in (60, 100, 150, 180):
        for domain, info in domain_details(z.iloc[:day]).items():
            a, b = series.iloc[day - 1][domain], info["score"]
            assert (pd.isna(a) and pd.isna(b)) or a == pytest.approx(b)


def test_action_cards_sorted_by_urgency():
    cards = build_cards(domain_details(compute_zscores(generate_demo("sleep_stress"))))
    assert cards and all(c["steps"] for c in cards)
    urgencies = [c["status"] for c in cards]
    assert urgencies == sorted(urgencies, key=lambda s: s != "rouge")


def test_no_cards_when_everything_is_normal():
    assert build_cards(domain_details(compute_zscores(generate_demo("normal")))) == []
