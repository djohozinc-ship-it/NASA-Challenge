"""Tests du suivi des alertes : ouverture, escalade, hystérésis, idempotence."""
import pytest

from src import demo, storage, tracker
from src.config import ESCALATION_DAYS, RESOLVE_DAYS
from src.detector import evaluate


def run_days(conn, aid, start, stop):
    """Fait avancer la démo et synchronise chaque jour. Retourne tous les changements."""
    log = []
    for _ in range(start, stop):
        df = storage.load_frame(conn, aid)
        _, details = evaluate(df)
        log += tracker.sync_alerts(conn, aid, details, df["date"].iloc[-1])
        demo.advance(conn, aid, 1)
    return log


def test_nominal_mission_creates_no_alerts(conn, astro):
    demo.load_scenario(conn, astro, "normal", 30)
    assert run_days(conn, astro, 30, 180) == []
    assert tracker.open_items(conn, astro) == []


def test_alert_opens_escalates_then_resolves(conn, astro):
    demo.load_scenario(conn, astro, "infection", 100)
    log = run_days(conn, astro, 100, 175)
    kinds = [c["kind"] for c in log]
    assert "alerte_ouverte" in kinds and "escalade_auto" in kinds and "alerte_resolue" in kinds
    assert kinds.index("alerte_ouverte") < kinds.index("escalade_auto") < kinds.index("alerte_resolue")
    assert tracker.open_items(conn, astro) == []


def test_red_alert_escalates_after_configured_delay(conn, astro):
    demo.load_scenario(conn, astro, "infection", 120)
    run_days(conn, astro, 120, 130)
    events = storage.list_events(conn, astro)
    opened = next(e for e in reversed(events) if e["kind"] == "alerte_ouverte")
    escal = next(e for e in reversed(events) if e["kind"] == "escalade_auto")
    gap = (__import__("pandas").Timestamp(escal["date"]) - __import__("pandas").Timestamp(opened["date"])).days
    assert gap == ESCALATION_DAYS["rouge"]


def test_sync_is_idempotent(conn, astro):
    demo.load_scenario(conn, astro, "infection", 126)
    df = storage.load_frame(conn, astro)
    _, details = evaluate(df)
    day = df["date"].iloc[-1]
    tracker.sync_alerts(conn, astro, details, day)
    n_events = len(storage.list_events(conn, astro))
    assert tracker.sync_alerts(conn, astro, details, day) == []
    assert len(storage.list_events(conn, astro)) == n_events


def test_user_action_prevents_auto_escalation(conn, astro):
    demo.load_scenario(conn, astro, "infection", 123)
    df = storage.load_frame(conn, astro)
    _, details = evaluate(df)
    tracker.sync_alerts(conn, astro, details, df["date"].iloc[-1])
    item = tracker.open_items(conn, astro)[0]
    tracker.set_state(conn, astro, item["id"], "fait", df["date"].iloc[-1], "Repos")
    run_days(conn, astro, 123, 126)
    states = {i["state"] for i in tracker.open_items(conn, astro)}
    assert "escalade" not in states


def test_cannot_set_invalid_or_unknown_state(conn, astro):
    with pytest.raises(ValueError):
        tracker.set_state(conn, astro, 999, "fait", "2026-01-01")
    with pytest.raises(ValueError):
        tracker.set_state(conn, astro, 1, "escalade", "2026-01-01")


def test_resolution_does_not_depend_on_how_often_we_look(conn, astro):
    """Sauter 14 jours d'un coup doit clore l'alerte, comme une consultation quotidienne."""
    demo.load_scenario(conn, astro, "infection", 125)
    df = storage.load_frame(conn, astro)
    _, details = evaluate(df)
    tracker.sync_alerts(conn, astro, details, df["date"].iloc[-1])
    assert tracker.open_items(conn, astro)
    demo.advance(conn, astro, 25)
    df = storage.load_frame(conn, astro)
    _, details = evaluate(df)
    changes = tracker.sync_alerts(conn, astro, details, df["date"].iloc[-1])
    assert [c["kind"] for c in changes if c["kind"] == "alerte_resolue"]
    assert tracker.open_items(conn, astro) == []


def test_alert_stays_open_until_enough_green_days(conn, astro):
    assert RESOLVE_DAYS >= 2
    demo.load_scenario(conn, astro, "infection", 125)
    df = storage.load_frame(conn, astro)
    _, details = evaluate(df)
    tracker.sync_alerts(conn, astro, details, df["date"].iloc[-1])
    demo.advance(conn, astro, 5)   # jour 130 : domaine encore orange
    df = storage.load_frame(conn, astro)
    _, details = evaluate(df)
    tracker.sync_alerts(conn, astro, details, df["date"].iloc[-1])
    assert tracker.open_items(conn, astro)
