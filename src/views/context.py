"""Contexte d'affichage : tout ce que les vues ont besoin de savoir d'un astronaute."""
from dataclasses import dataclass, field

import pandas as pd

from src import storage, tracker
from src.detector import BASELINE_DAYS, calibration_progress, evaluate
from src.summary import indicator_rows, recent_and_reference


@dataclass
class Ctx:
    conn: object
    astronaut: dict
    df: pd.DataFrame
    z: pd.DataFrame
    details: dict
    as_of: pd.Timestamp = None
    day: int = 0
    calibrating: bool = True
    progress: float = 0.0
    recent: pd.Series = None
    reference: pd.Series = None
    rows: list = field(default_factory=list)
    items: list = field(default_factory=list)       # alertes ouvertes
    changes: list = field(default_factory=list)     # changements de cette synchronisation

    @property
    def empty(self):
        return len(self.df) == 0

    @property
    def aid(self):
        return self.astronaut["id"]

    @property
    def n_alerts(self):
        return sum(1 for d in self.details.values() if d["status"] in ("rouge", "orange"))


def build_context(conn, astronaut):
    """Charge les données, évalue la santé et synchronise le suivi des alertes."""
    df = storage.load_frame(conn, astronaut["id"])
    z, details = evaluate(df)
    as_of = df["date"].iloc[-1] if len(df) else None
    changes = tracker.sync_alerts(conn, astronaut["id"], details, as_of) if len(df) else []
    recent, reference = recent_and_reference(df)
    return Ctx(
        conn=conn, astronaut=astronaut, df=df, z=z, details=details, as_of=as_of,
        day=len(df), calibrating=len(df) < BASELINE_DAYS, progress=calibration_progress(df),
        recent=recent, reference=reference, rows=indicator_rows(df, z),
        items=tracker.open_items(conn, astronaut["id"]) if len(df) else [], changes=changes,
    )
