"""Tests de la persistance, de la validation des entrées et du mode démonstration."""
import numpy as np
import pandas as pd
import pytest

from src import demo, storage
from src.ingest import add_checkin, import_csv, validate_value


def test_create_profile_rules(conn):
    storage.create_astronaut(conn, "A")
    with pytest.raises(ValueError):
        storage.create_astronaut(conn, "A")
    with pytest.raises(ValueError):
        storage.create_astronaut(conn, "   ")
    with pytest.raises(ValueError):
        storage.create_astronaut(conn, "x" * 61)


def test_checkin_roundtrip_and_overwrite(conn, astro):
    assert add_checkin(conn, astro, "2026-03-01", {"mood": "7,5", "weight": 75})[0] == 2
    assert add_checkin(conn, astro, "2026-03-01", {"mood": 6.0})[0] == 1
    df = storage.load_frame(conn, astro)
    assert df.loc[0, "mood"] == 6.0 and df.loc[0, "weight"] == 75


def test_checkin_is_all_or_nothing(conn, astro):
    written, errors = add_checkin(conn, astro, "2026-03-01", {"mood": 7, "stress": 55})
    assert written == 0 and errors
    assert storage.load_frame(conn, astro).empty


@pytest.mark.parametrize("raw", ["abc", "", None, float("nan"), float("inf"), 999])
def test_invalid_values_are_rejected(raw):
    value, err = validate_value("resting_hr", raw)
    assert value is None and err


def test_frame_has_one_row_per_calendar_day(conn, astro):
    add_checkin(conn, astro, "2026-03-01", {"mood": 7})
    add_checkin(conn, astro, "2026-03-05", {"mood": 6})
    df = storage.load_frame(conn, astro)
    assert len(df) == 5 and df["mood"].isna().sum() == 3


def test_import_csv_reports_problems_without_crashing(conn, astro):
    raw = b"date;mood;foo;weight\n2026-05-01;7,2;1;74.5\nbad;1;1;1\n2026-05-02;abc;1;999\n"
    report = import_csv(conn, astro, raw)
    assert report.values_imported == 2 and report.rows_imported == 1
    assert len(report.rejected) == 3 and report.warnings


@pytest.mark.parametrize("raw", [b"", b"\x00\x01\x02", b"foo,bar\n1,2\n", b"date\n2026-01-01\n"])
def test_garbage_files_never_raise(conn, astro, raw):
    report = import_csv(conn, astro, raw)
    assert not report.ok and report.rejected


def test_import_is_idempotent(conn, astro):
    raw = b"date,mood\n2026-05-01,7\n2026-05-02,6\n"
    import_csv(conn, astro, raw)
    import_csv(conn, astro, raw)
    assert len(storage.load_frame(conn, astro)) == 2


def test_demo_load_and_advance(conn, astro):
    demo.load_scenario(conn, astro, "sleep_stress", 40)
    assert demo.mission_day(conn, astro) == 40
    assert demo.advance(conn, astro, 7) == 47
    df = storage.load_frame(conn, astro)
    assert len(df) == 47 and df.drop(columns="date").isna().sum().sum() == 0


def test_advance_refuses_real_profiles(conn, astro):
    with pytest.raises(ValueError):
        demo.advance(conn, astro, 1)


def test_delete_cascades(conn, astro):
    add_checkin(conn, astro, "2026-03-01", {"mood": 7})
    storage.log_event(conn, astro, "2026-03-01", "test")
    storage.delete_astronaut(conn, astro)
    for table in ("measurements", "events"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_backup_is_a_valid_database(conn, astro, tmp_path):
    add_checkin(conn, astro, "2026-03-01", {"mood": 7})
    dest = storage.vacuum_backup(conn, tmp_path / "bak" / "copy.db")
    other = storage.connect(dest)
    assert len(storage.load_frame(other, astro)) == 1
    other.close()
