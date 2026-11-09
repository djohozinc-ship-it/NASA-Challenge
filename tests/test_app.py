"""Tests de bout en bout de l'interface Streamlit (sans navigateur)."""
import datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src import storage

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("BIOSPACE_DB", str(tmp_path / "app.db"))
    monkeypatch.setenv("BIOSPACE_LOG", str(tmp_path / "app.log"))
    return AppTest.from_file(APP, default_timeout=120).run()


def test_first_launch_shows_welcome(app):
    assert not app.exception
    assert any("Bienvenue" in m.value for m in app.markdown)


def test_demo_profile_flow(app):
    app.sidebar.text_input(key="new_name").set_value("Demo")
    app.sidebar.radio(key="new_kind").set_value("Démonstration (scénario simulé)").run()
    app.sidebar.selectbox(key="new_scenario").set_value("infection")
    app.sidebar.button(key="create_profile").click().run()
    assert not app.exception
    app.sidebar.button(key="adv7").click().run()
    assert not app.exception
    assert any("Actions" in t.label for t in app.tabs)


def test_real_profile_checkin_and_critical_alert(app):
    app.sidebar.text_input(key="new_name").set_value("Réel")
    app.sidebar.button(key="create_profile").click().run()
    app.date_input[0].set_value(datetime.date(2026, 3, 1))
    [w for w in app.number_input if w.key.endswith("_bp_systolic")][0].set_value(170)
    [b for b in app.button if b.label == "Enregistrer le bilan"][0].click().run()
    assert not app.exception
    conn = storage.connect()
    aid = storage.list_astronauts(conn)[0]["id"]
    assert storage.load_frame(conn, aid).loc[0, "bp_systolic"] == 170
    assert any("action requise" in m.value for m in app.markdown)
    conn.close()


def test_pdf_generation_from_ui(app):
    app.sidebar.text_input(key="new_name").set_value("Demo")
    app.sidebar.radio(key="new_kind").set_value("Démonstration (scénario simulé)").run()
    app.sidebar.button(key="create_profile").click().run()
    [b for b in app.button if b.label == "Générer le rapport PDF"][0].click().run()
    assert not app.exception
