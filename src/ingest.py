"""Saisie et import de données avec validation stricte.

Toute valeur est contrôlée (nombre, bornes plausibles) avant d'entrer en base.
Un fichier mal formé ne casse jamais l'application : les lignes ou cellules
rejetées sont listées dans le rapport d'import.
"""
import io
import logging
from dataclasses import dataclass, field

import pandas as pd

from src.config import INDICATORS, LABELS, UNITS, VALID
from src.storage import upsert_measurements

log = logging.getLogger("biospace")

MAX_ROWS = 20000
MAX_BYTES = 5_000_000
IGNORED_COLUMNS = {"dose_cumulative"}   # recalculée à partir du débit de dose


@dataclass
class ImportReport:
    rows_read: int = 0
    rows_imported: int = 0
    values_imported: int = 0
    rejected: list = field(default_factory=list)   # (ligne, raison)
    warnings: list = field(default_factory=list)

    @property
    def ok(self):
        return self.values_imported > 0


def parse_number(raw):
    """Convertit une saisie en float (virgule décimale acceptée). Lève ValueError."""
    if raw is None:
        raise ValueError("valeur vide")
    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        text = str(raw).strip().replace(",", ".").replace(" ", "")
        if not text:
            raise ValueError("valeur vide")
        value = float(text)
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError("valeur non finie")
    return value


def validate_value(indicator, raw):
    """Retourne (valeur, None) si valide, sinon (None, message d'erreur)."""
    if indicator not in INDICATORS:
        return None, f"indicateur inconnu : {indicator}"
    try:
        value = parse_number(raw)
    except ValueError:
        return None, f"{LABELS[indicator]} : « {raw} » n'est pas un nombre"
    low, high = VALID[indicator]
    if not (low <= value <= high):
        u = UNITS[indicator]
        sep = "" if u.startswith("/") or not u else " "
        return None, (f"{LABELS[indicator]} : {value:g}{sep}{u} est hors des bornes "
                      f"plausibles ({low:g} à {high:g}{sep}{u})")
    return value, None


def add_checkin(conn, astronaut_id, date, values, source="saisie"):
    """Enregistre le bilan d'un jour. values : {indicateur: valeur ou None}.

    Tout ou rien : si une valeur est invalide, rien n'est écrit.
    Retourne (nombre de valeurs écrites, liste d'erreurs).
    """
    clean, errors = {}, []
    for indicator, raw in values.items():
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            continue
        value, err = validate_value(indicator, raw)
        if err:
            errors.append(err)
        else:
            clean[indicator] = value
    if errors:
        return 0, errors
    if not clean:
        return 0, ["Aucune valeur saisie."]
    day = pd.Timestamp(date).date().isoformat()
    n = upsert_measurements(conn, astronaut_id, [(day, i, v, source) for i, v in clean.items()])
    log.info("Bilan enregistré : astronaute=%s date=%s valeurs=%d", astronaut_id, day, n)
    return n, []


def import_csv(conn, astronaut_id, source, source_name="import"):
    """Importe un CSV (chemin, fichier ou octets). Retourne un ImportReport."""
    report = ImportReport()
    try:
        if isinstance(source, (bytes, bytearray)):
            if len(source) > MAX_BYTES:
                report.rejected.append((0, f"fichier trop volumineux (> {MAX_BYTES // 1_000_000} Mo)"))
                return report
            buffer = io.StringIO(source.decode("utf-8-sig", errors="replace"))
        elif hasattr(source, "read"):
            return import_csv(conn, astronaut_id, source.read(), source_name)
        else:
            with open(source, "rb") as fh:
                return import_csv(conn, astronaut_id, fh.read(), source_name)
        df = pd.read_csv(buffer, sep=None, engine="python", dtype=str, skipinitialspace=True)
    except Exception as exc:   # fichier illisible, vide, encodage cassé...
        log.warning("Import illisible (%s) : %s", source_name, exc)
        report.rejected.append((0, f"fichier illisible : {exc}"))
        return report

    df.columns = [str(c).strip().lower() for c in df.columns]
    if "date" not in df.columns:
        report.rejected.append((0, "colonne « date » absente"))
        return report
    if len(df) > MAX_ROWS:
        report.rejected.append((0, f"trop de lignes ({len(df)} > {MAX_ROWS})"))
        return report

    known = [c for c in df.columns if c in INDICATORS]
    unknown = [c for c in df.columns if c not in INDICATORS and c != "date"
               and c not in IGNORED_COLUMNS]
    if unknown:
        report.warnings.append("Colonnes ignorées : " + ", ".join(unknown))
    if not known:
        report.rejected.append((0, "aucune colonne d'indicateur reconnue"))
        return report

    report.rows_read = len(df)
    rows, seen = [], set()
    for pos, rec in enumerate(df.to_dict("records")):
        line = pos + 2   # en-tête = ligne 1
        try:
            day = pd.to_datetime(rec["date"], dayfirst=False, errors="raise").date().isoformat()
        except Exception:
            report.rejected.append((line, f"date invalide : « {rec['date']} »"))
            continue
        if day in seen:
            report.warnings.append(f"Date en double {day} (ligne {line}) : la dernière valeur est conservée")
        seen.add(day)
        kept = 0
        for c in known:
            raw = rec.get(c)
            if raw is None or (isinstance(raw, float) and raw != raw) or str(raw).strip() == "":
                continue
            value, err = validate_value(c, raw)
            if err:
                report.rejected.append((line, err))
            else:
                rows.append((day, c, value, "import"))
                kept += 1
        report.rows_imported += bool(kept)

    if rows:
        report.values_imported = upsert_measurements(conn, astronaut_id, rows)
    log.info("Import %s : %d lignes, %d valeurs, %d rejets",
             source_name, report.rows_imported, report.values_imported, len(report.rejected))
    return report
