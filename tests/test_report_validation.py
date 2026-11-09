"""Tests des rapports PDF/CSV et de la validation."""
import io

import pandas as pd
import pytest

from src import demo, report, storage, tracker, validation
from src.detector import evaluate


@pytest.fixture
def filled(conn, astro):
    demo.load_scenario(conn, astro, "sleep_stress", 60)
    for _ in range(60, 130):
        df = storage.load_frame(conn, astro)
        _, details = evaluate(df)
        tracker.sync_alerts(conn, astro, details, df["date"].iloc[-1])
        demo.advance(conn, astro, 1)
    df = storage.load_frame(conn, astro)
    z, details = evaluate(df)
    tracker.sync_alerts(conn, astro, details, df["date"].iloc[-1])
    return df, z, details


def test_pdf_is_valid_and_contains_key_sections(conn, astro, filled):
    df, z, details = filled
    pdf = report.build_pdf(storage.get_astronaut(conn, astro),
                           df, z, details, tracker.all_items(conn, astro),
                           storage.list_events(conn, astro), df["date"].iloc[-1])
    assert pdf.startswith(b"%PDF") and len(pdf) > 5000
    try:
        from pypdf import PdfReader
    except ImportError:
        return
    text = " ".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages)
    assert "Testeur" in text and "Journal" in text


def test_pdf_handles_non_latin_names_and_empty_journal(conn, astro, filled):
    df, z, details = filled
    pdf = report.build_pdf({"id": astro, "name": "Σ-<b>Test</b> & Co 宇宙"}, df, z, details, [], [],
                           df["date"].iloc[-1])
    assert pdf.startswith(b"%PDF")


def test_csv_exports_roundtrip(filled):
    df, _, _ = filled
    raw = report.measurements_csv(df)
    back = pd.read_csv(io.BytesIO(raw))
    assert len(back) == len(df) and "resting_hr" in back.columns
    assert report.events_csv([]).startswith(b"\xef\xbb\xbf")


def test_false_alarm_rate_is_low():
    stats = validation.false_alarm_stats(n_seeds=15)
    assert stats["alert_days_pct"] < 8 and stats["red_days_pct"] < 0.5


def test_false_alarm_rate_robust_to_missing_data():
    stats = validation.false_alarm_stats(n_seeds=15, missing_rate=0.2)
    assert stats["alert_days_pct"] < 10 and stats["red_days_pct"] < 1


@pytest.mark.parametrize("scenario", list(validation.EXPECTED))
def test_every_scenario_is_detected(scenario):
    res = validation.detection_stats(scenario, n_seeds=10)
    assert res["detected_pct"] == 100
    assert res["median_delay"] < 60
