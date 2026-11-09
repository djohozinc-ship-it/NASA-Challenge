import pytest

from src import storage


@pytest.fixture
def conn(tmp_path, monkeypatch):
    """Base SQLite temporaire, isolée pour chaque test."""
    monkeypatch.setenv("BIOSPACE_DB", str(tmp_path / "test.db"))
    monkeypatch.setenv("BIOSPACE_LOG", str(tmp_path / "test.log"))
    connection = storage.connect()
    yield connection
    connection.close()


@pytest.fixture
def astro(conn):
    return storage.create_astronaut(conn, "Testeur")
