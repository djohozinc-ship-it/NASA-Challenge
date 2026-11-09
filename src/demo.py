"""Mode démonstration : charge un scénario simulé et fait avancer la mission jour par jour."""
import pandas as pd

from src.config import SCENARIO_NAMES
from src.generator import generate_demo
from src.storage import clear_astronaut_data, date_range, get_astronaut, upsert_measurements


def _rows(df):
    out = []
    for rec in df.to_dict("records"):
        day = pd.Timestamp(rec["date"]).date().isoformat()
        for key, value in rec.items():
            if key not in ("date", "dose_cumulative") and value == value:
                out.append((day, key, value, "simulation"))
    return out


def load_scenario(conn, astronaut_id, scenario, upto_day=30):
    """Remplace les données du profil par les `upto_day` premiers jours du scénario."""
    if scenario not in SCENARIO_NAMES:
        raise ValueError(f"Scénario inconnu : {scenario}")
    full = generate_demo(scenario)
    clear_astronaut_data(conn, astronaut_id)
    conn.execute("UPDATE astronauts SET is_demo = 1, scenario = ? WHERE id = ?",
                 (scenario, astronaut_id))
    conn.commit()
    upsert_measurements(conn, astronaut_id, _rows(full.iloc[:upto_day]))
    return upto_day


def mission_day(conn, astronaut_id):
    first, last = date_range(conn, astronaut_id)
    return 0 if first is None else (last - first).days + 1


def advance(conn, astronaut_id, days=1):
    """Ajoute les `days` jours suivants du scénario. Retourne le nouveau jour de mission."""
    astro = get_astronaut(conn, astronaut_id)
    if not astro or not astro["is_demo"] or not astro["scenario"]:
        raise ValueError("Ce profil n'est pas un profil de démonstration.")
    full = generate_demo(astro["scenario"])
    done = mission_day(conn, astronaut_id)
    new = full.iloc[done:done + days]
    if len(new):
        upsert_measurements(conn, astronaut_id, _rows(new))
    return mission_day(conn, astronaut_id)


def scenario_length(scenario):
    return len(generate_demo(scenario))
