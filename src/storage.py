"""Persistance locale (SQLite) : profils, mesures, journal d'événements, actions.

Tout est stocké dans un seul fichier, sans serveur ni réseau. Le chemin se règle
avec la variable d'environnement BIOSPACE_DB (utile pour les tests et l'exécutable).
"""
import logging
import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import INDICATORS

log = logging.getLogger("biospace")

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "biospace.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS astronauts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE,
    created   TEXT NOT NULL,
    is_demo   INTEGER NOT NULL DEFAULT 0,
    scenario  TEXT
);
CREATE TABLE IF NOT EXISTS measurements (
    astronaut_id INTEGER NOT NULL REFERENCES astronauts(id) ON DELETE CASCADE,
    date         TEXT NOT NULL,
    indicator    TEXT NOT NULL,
    value        REAL NOT NULL,
    source       TEXT NOT NULL DEFAULT 'saisie',
    PRIMARY KEY (astronaut_id, date, indicator)
);
CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    astronaut_id INTEGER NOT NULL REFERENCES astronauts(id) ON DELETE CASCADE,
    date         TEXT NOT NULL,
    ts           TEXT NOT NULL,
    kind         TEXT NOT NULL,
    domain       TEXT,
    status       TEXT,
    detail       TEXT
);
CREATE TABLE IF NOT EXISTS action_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    astronaut_id INTEGER NOT NULL REFERENCES astronauts(id) ON DELETE CASCADE,
    domain       TEXT NOT NULL,
    status       TEXT NOT NULL,
    state        TEXT NOT NULL,
    opened       TEXT NOT NULL,
    updated      TEXT NOT NULL,
    closed       TEXT,
    note         TEXT
);
CREATE INDEX IF NOT EXISTS idx_meas ON measurements (astronaut_id, date);
CREATE INDEX IF NOT EXISTS idx_events ON events (astronaut_id, date);
CREATE INDEX IF NOT EXISTS idx_actions ON action_items (astronaut_id, domain);
"""


def db_path():
    return Path(os.environ.get("BIOSPACE_DB") or DEFAULT_DB)


def connect(path=None):
    """Ouvre la base (créée si absente) et garantit le schéma."""
    path = Path(path) if path else db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def _now():
    return datetime.now().isoformat(timespec="seconds")


# --- Profils ---
def create_astronaut(conn, name, is_demo=False, scenario=None):
    name = (name or "").strip()
    if not name:
        raise ValueError("Le nom du profil est vide.")
    if len(name) > 60:
        raise ValueError("Le nom du profil dépasse 60 caractères.")
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO astronauts (name, created, is_demo, scenario) VALUES (?,?,?,?)",
                (name, _now(), int(is_demo), scenario),
            )
    except sqlite3.IntegrityError:
        raise ValueError(f"Un profil nommé « {name} » existe déjà.") from None
    log.info("Profil créé : %s (id=%s)", name, cur.lastrowid)
    return cur.lastrowid


def list_astronauts(conn):
    rows = conn.execute("SELECT * FROM astronauts ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def get_astronaut(conn, astronaut_id):
    row = conn.execute("SELECT * FROM astronauts WHERE id = ?", (astronaut_id,)).fetchone()
    return dict(row) if row else None


def delete_astronaut(conn, astronaut_id):
    with conn:
        conn.execute("DELETE FROM astronauts WHERE id = ?", (astronaut_id,))
    log.info("Profil supprimé : id=%s", astronaut_id)


# --- Mesures ---
def upsert_measurements(conn, astronaut_id, rows):
    """rows : itérable de (date ISO, indicateur, valeur, source). Retourne le nombre écrit."""
    data = [(astronaut_id, str(d), i, float(v), s) for d, i, v, s in rows if i in INDICATORS]
    with conn:
        conn.executemany(
            "INSERT INTO measurements (astronaut_id, date, indicator, value, source) "
            "VALUES (?,?,?,?,?) ON CONFLICT(astronaut_id, date, indicator) "
            "DO UPDATE SET value = excluded.value, source = excluded.source",
            data,
        )
    return len(data)


def date_range(conn, astronaut_id):
    row = conn.execute(
        "SELECT MIN(date) AS first, MAX(date) AS last FROM measurements WHERE astronaut_id = ?",
        (astronaut_id,),
    ).fetchone()
    if row["first"] is None:
        return None, None
    return pd.Timestamp(row["first"]), pd.Timestamp(row["last"])


def load_frame(conn, astronaut_id):
    """DataFrame d'un astronaute : une ligne par jour calendaire, NaN si manquant.

    Colonnes : date, un indicateur par colonne, dose_cumulative.
    """
    cols = list(INDICATORS)
    rows = conn.execute(
        "SELECT date, indicator, value FROM measurements WHERE astronaut_id = ?",
        (astronaut_id,),
    ).fetchall()
    if not rows:
        return pd.DataFrame(columns=["date"] + cols + ["dose_cumulative"]).astype(
            {"date": "datetime64[ns]"}
        )
    long = pd.DataFrame(rows, columns=["date", "indicator", "value"])
    long["date"] = pd.to_datetime(long["date"])
    wide = long.pivot(index="date", columns="indicator", values="value")
    wide = wide.reindex(columns=cols)
    full = pd.date_range(wide.index.min(), wide.index.max(), freq="D")
    wide = wide.reindex(full)
    wide.index.name = "date"
    wide = wide.reset_index()
    wide["dose_cumulative"] = wide["dose_rate"].fillna(0).cumsum()
    return wide


# --- Journal d'événements ---
def log_event(conn, astronaut_id, date, kind, domain=None, status=None, detail=None):
    with conn:
        conn.execute(
            "INSERT INTO events (astronaut_id, date, ts, kind, domain, status, detail) "
            "VALUES (?,?,?,?,?,?,?)",
            (astronaut_id, str(date)[:10], _now(), kind, domain, status, detail),
        )


def list_events(conn, astronaut_id, limit=200):
    rows = conn.execute(
        "SELECT * FROM events WHERE astronaut_id = ? ORDER BY id DESC LIMIT ?",
        (astronaut_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def clear_astronaut_data(conn, astronaut_id):
    """Efface mesures, événements et actions d'un profil (conserve le profil)."""
    with conn:
        for table in ("measurements", "events", "action_items"):
            conn.execute(f"DELETE FROM {table} WHERE astronaut_id = ?", (astronaut_id,))


def vacuum_backup(conn, dest):
    """Copie cohérente de la base vers `dest` (sauvegarde)."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    with closing(sqlite3.connect(dest)) as out:
        conn.backup(out)
    return dest
