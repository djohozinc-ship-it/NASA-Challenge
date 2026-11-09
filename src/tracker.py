"""Suivi des alertes et des actions : boucle complète alerte -> action -> résolution.

Cycle de vie d'une alerte (une alerte ouverte par astronaute et par domaine) :

    à faire --> fait            (l'astronaute a appliqué les conseils)
            --> reporté         (l'astronaute repousse)
            --> signalé         (l'astronaute a contacté l'équipe médicale)
            --> escaladé        (automatique : trop longtemps sans action)
    résolue                     (automatique : le domaine est normal depuis RESOLVE_DAYS jours consécutifs,
                                 mesuré sur les données, donc indépendant de la fréquence de consultation)

Les dates sont celles de la mission (dernière mesure), pas l'horloge de l'ordinateur,
ce qui rend le mode démonstration cohérent. La synchronisation est idempotente.
"""
import logging

import pandas as pd

from src.config import ESCALATION_DAYS, RESOLVE_DAYS
from src.storage import log_event

log = logging.getLogger("biospace")

STATES = {
    "a_faire": "À faire",
    "fait": "Fait",
    "reporte": "Reporté",
    "signale": "Signalé à l'équipe médicale",
    "escalade": "Escaladé automatiquement",
    "resolue": "Résolue (retour à la normale)",
}
OPEN_STATES = ("a_faire", "reporte", "signale", "escalade", "fait")
SEVERITY = {"orange": 1, "rouge": 2}


def _day(value):
    return pd.Timestamp(value).date().isoformat()


def open_items(conn, astronaut_id):
    rows = conn.execute(
        "SELECT * FROM action_items WHERE astronaut_id = ? AND state != 'resolue' "
        "ORDER BY CASE status WHEN 'rouge' THEN 0 ELSE 1 END, opened",
        (astronaut_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def all_items(conn, astronaut_id, limit=200):
    rows = conn.execute(
        "SELECT * FROM action_items WHERE astronaut_id = ? ORDER BY id DESC LIMIT ?",
        (astronaut_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def days_open(item, as_of):
    return (pd.Timestamp(as_of) - pd.Timestamp(item["opened"])).days


def sync_alerts(conn, astronaut_id, details, as_of):
    """Aligne les actions suivies sur l'état courant des domaines.

    - ouvre une alerte pour tout domaine orange/rouge sans alerte ouverte ;
    - relève la gravité si orange -> rouge ;
    - clôture (résolue) quand le domaine est vert depuis RESOLVE_DAYS jours consécutifs ;
    - escalade automatiquement après ESCALATION_DAYS[gravité] jours sans action.

    Retourne la liste des changements (dict) effectués pendant cet appel.
    """
    as_of = _day(as_of)
    changes = []
    existing = {i["domain"]: i for i in open_items(conn, astronaut_id)}

    for domain, info in details.items():
        status = info["status"]
        item = existing.get(domain)

        if status in SEVERITY:
            if item is None:
                with conn:
                    cur = conn.execute(
                        "INSERT INTO action_items (astronaut_id, domain, status, state, opened, updated) "
                        "VALUES (?,?,?,?,?,?)",
                        (astronaut_id, domain, status, "a_faire", as_of, as_of),
                    )
                log_event(conn, astronaut_id, as_of, "alerte_ouverte", domain, status,
                          "Alerte ouverte" + (" (seuil critique)" if info.get("critical") else ""))
                changes.append({"kind": "alerte_ouverte", "domain": domain, "status": status,
                                "id": cur.lastrowid})
                item = dict(conn.execute("SELECT * FROM action_items WHERE id = ?",
                                         (cur.lastrowid,)).fetchone())
            elif SEVERITY[status] > SEVERITY[item["status"]]:
                with conn:
                    conn.execute(
                        "UPDATE action_items SET status = ?, state = CASE WHEN state = 'fait' "
                        "THEN 'a_faire' ELSE state END, updated = ? WHERE id = ?",
                        (status, as_of, item["id"]))
                log_event(conn, astronaut_id, as_of, "alerte_aggravee", domain, status,
                          f"{item['status']} -> {status}")
                changes.append({"kind": "alerte_aggravee", "domain": domain, "status": status,
                                "id": item["id"]})
                item = dict(conn.execute("SELECT * FROM action_items WHERE id = ?",
                                         (item["id"],)).fetchone())

            elif SEVERITY[status] < SEVERITY[item["status"]]:
                with conn:
                    conn.execute("UPDATE action_items SET status = ?, updated = ? WHERE id = ?",
                                 (status, as_of, item["id"]))
                log_event(conn, astronaut_id, as_of, "alerte_attenuee", domain, status,
                          f"{item['status']} -> {status}")
                changes.append({"kind": "alerte_attenuee", "domain": domain, "status": status,
                                "id": item["id"]})
                item = dict(conn.execute("SELECT * FROM action_items WHERE id = ?",
                                         (item["id"],)).fetchone())

            limit = ESCALATION_DAYS[item["status"]]
            if item["state"] in ("a_faire", "reporte") and days_open(item, as_of) >= limit:
                with conn:
                    conn.execute("UPDATE action_items SET state = 'escalade', updated = ? WHERE id = ?",
                                 (as_of, item["id"]))
                log_event(conn, astronaut_id, as_of, "escalade_auto", domain, item["status"],
                          f"Aucune action après {limit} jour(s) : remontée à l'équipe médicale")
                changes.append({"kind": "escalade_auto", "domain": domain,
                                "status": item["status"], "id": item["id"]})

        elif status == "vert" and item is not None and info.get("green_streak", 0) >= RESOLVE_DAYS:
            with conn:
                conn.execute("UPDATE action_items SET state = 'resolue', closed = ?, updated = ? "
                             "WHERE id = ?", (as_of, as_of, item["id"]))
            log_event(conn, astronaut_id, as_of, "alerte_resolue", domain, "vert",
                      f"Retour à la normale ({RESOLVE_DAYS} jours consécutifs)")
            changes.append({"kind": "alerte_resolue", "domain": domain, "status": "vert",
                            "id": item["id"]})
    return changes


def set_state(conn, astronaut_id, item_id, state, as_of, note=None):
    """Enregistre l'action de l'astronaute sur une alerte."""
    if state not in ("fait", "reporte", "signale"):
        raise ValueError(f"État non modifiable manuellement : {state}")
    row = conn.execute("SELECT * FROM action_items WHERE id = ? AND astronaut_id = ?",
                       (item_id, astronaut_id)).fetchone()
    if row is None:
        raise ValueError("Alerte introuvable.")
    if row["state"] == "resolue":
        raise ValueError("Cette alerte est déjà résolue.")
    day = _day(as_of)
    with conn:
        conn.execute("UPDATE action_items SET state = ?, updated = ?, note = COALESCE(?, note) "
                     "WHERE id = ?", (state, day, (note or None), item_id))
    log_event(conn, astronaut_id, day, f"action_{state}", row["domain"], row["status"],
              note or STATES[state])
    return state
