"""Éléments visuels réutilisables du dashboard (HTML/CSS, 100 % hors ligne).

Aucune police, image ou script externe : l'interface fonctionne sans réseau.
"""
from html import escape

COLORS = {"vert": "#2ECC71", "orange": "#F39C12", "rouge": "#E5484D", "inconnu": "#7F8C9B"}
STATUS_LABELS = {
    "vert": "Normal",
    "orange": "À surveiller",
    "rouge": "Action requise",
    "inconnu": "Calibration",
}

CSS = """
<style>
.block-container {padding-top: 3.5rem; max-width: 1280px;}
#MainMenu, footer {visibility: hidden;}
html, body, [class*="css"] {
    font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* En-tête de mission */
.topbar {display: flex; justify-content: space-between; align-items: center;
         gap: 16px; flex-wrap: wrap; margin-bottom: 4px;}
.brand {font-size: 1.7rem; font-weight: 700; letter-spacing: -0.01em; color: #EAF0FA;}
.brand span {color: #4F8BF9;}
.subtitle {font-size: 0.85rem; color: #8FA0BC; margin-bottom: 14px;}
.autonomy {display: inline-flex; align-items: center; gap: 8px; font-size: 0.75rem;
           font-weight: 600; letter-spacing: 0.04em; color: #2ECC71;
           background: #2ECC7118; border: 1px solid #2ECC7155;
           padding: 6px 12px; border-radius: 999px;}
.dot {width: 8px; height: 8px; border-radius: 50%; display: inline-block;}

/* Bandeau de synthèse */
.banner {border-radius: 10px; padding: 14px 18px; margin: 6px 0 18px 0;
         font-weight: 600; display: flex; align-items: center; gap: 10px;}

/* Cartes de domaine */
.card {background: #131C2E; border: 1px solid #1F2A40; border-radius: 12px;
       padding: 16px 18px 10px 18px; margin-bottom: 14px; min-height: 290px;}
.card-head {display: flex; justify-content: space-between; align-items: center;
            flex-wrap: wrap; gap: 6px; margin-bottom: 10px;}
.card-title {font-size: 0.72rem; color: #A9B7CF; text-transform: uppercase;
             letter-spacing: 0.05em; font-weight: 600;}
.badge {font-size: 0.66rem; font-weight: 700; padding: 3px 10px; border-radius: 12px;
        white-space: nowrap;}
.row {display: flex; justify-content: space-between; align-items: baseline;
      padding: 8px 0; border-top: 1px solid #1F2A40;}
.row-label {flex: 1; padding-right: 8px; font-size: 0.78rem; color: #8FA0BC; display: flex; align-items: center; gap: 7px;}
.row-value {font-size: 1.15rem; font-weight: 600; color: #EAF0FA; white-space: nowrap; text-align: right;}
.row-unit {font-size: 0.72rem; color: #8FA0BC; font-weight: 400;}
.row-ref {font-size: 0.7rem; color: #6C7C99; text-align: right;}

/* Carte d'information */
.infocard {background: linear-gradient(160deg, #131C2E, #0F1829); border: 1px dashed #2A3956;
           border-radius: 12px; padding: 16px 18px; margin-bottom: 14px; min-height: 290px;}
.infocard h4 {margin: 0 0 8px 0; font-size: 0.78rem; color: #A9B7CF;
              text-transform: uppercase; letter-spacing: 0.08em;}
.infocard p {font-size: 0.82rem; color: #8FA0BC; line-height: 1.5; margin: 0 0 8px 0;}

/* Alertes prioritaires */
.alert {background: #131C2E; border: 1px solid #1F2A40; border-radius: 10px;
        padding: 12px 14px; margin-bottom: 10px;}
.alert-title {font-weight: 600; color: #EAF0FA; font-size: 0.95rem;}
.alert-sub {font-size: 0.8rem; color: #8FA0BC; margin-top: 4px;}
.ok {background: #2ECC7112; border: 1px solid #2ECC7144; color: #2ECC71;
     border-radius: 10px; padding: 16px; font-weight: 500;}
</style>
"""


def _badge(status):
    color = COLORS[status]
    return (f'<span class="badge" style="background:{color}22; color:{color};">'
            f'{STATUS_LABELS[status]}</span>')


def header(title, subtitle):
    """En-tête : titre, sous-titre et badge de mode autonome."""
    return (
        '<div class="topbar">'
        f'<div class="brand">{title}</div>'
        '<div class="autonomy"><span class="dot" style="background:#2ECC71;"></span>'
        'MODE AUTONOME · LIAISON SOL NON REQUISE</div>'
        '</div>'
        f'<div class="subtitle">{escape(subtitle)}</div>'
    )


def status_card(domain, status, rows):
    """Carte d'un domaine physiologique.

    rows : liste de dict(label, value, unit, ref, status) — un par indicateur.
    """
    color = COLORS[status]
    body = ""
    for r in rows:
        dot = COLORS[r["status"]]
        unit = f' <span class="row-unit">{escape(r["unit"])}</span>' if r["unit"] else ""
        body += (
            '<div class="row">'
            f'<div class="row-label"><span class="dot" style="background:{dot};"></span>'
            f'{escape(r["label"])}</div>'
            f'<div><div class="row-value">{r["value"]}{unit}</div>'
            f'<div class="row-ref">réf. {r["ref"]}</div></div>'
            '</div>'
        )
    return (
        f'<div class="card" style="border-left: 4px solid {color};">'
        f'<div class="card-head"><div class="card-title">{escape(domain)}</div>'
        f'{_badge(status)}</div>{body}</div>'
    )


def autonomy_card():
    """Carte explicative du fonctionnement hors ligne."""
    return (
        '<div class="infocard"><h4>Autonomie de mission</h4>'
        '<p>Tout le calcul s\'effectue à bord : aucune donnée n\'est envoyée '
        'au réseau terrestre et aucune connexion n\'est nécessaire.</p>'
        '<p>La référence de chaque astronaute est apprise sur ses propres '
        'données, avant l\'alerte, sans modèle distant.</p>'
        '<p style="margin-bottom:0;">Les alertes restent actives en cas de '
        'coupure de la liaison sol.</p></div>'
    )


def banner(status, text):
    """Bandeau de synthèse en haut de page."""
    color = COLORS[status]
    return (f'<div class="banner" style="background:{color}1A; '
            f'border:1px solid {color}; color:{color};">{text}</div>')


def alert_item(domain, status, detail):
    color = COLORS[status]
    return (f'<div class="alert" style="border-left:4px solid {color};">'
            f'<div class="alert-title">{escape(domain)} {_badge(status)}</div>'
            f'<div class="alert-sub">{escape(detail)}</div></div>')


STATE_COLORS = {"a_faire": "#F39C12", "fait": "#2ECC71", "reporte": "#7F8C9B",
                "signale": "#4F8BF9", "escalade": "#E5484D", "resolue": "#2ECC71"}


def state_chip(state, label):
    color = STATE_COLORS.get(state, "#7F8C9B")
    return (f'<span class="badge" style="background:{color}22; color:{color}; '
            f'border:1px solid {color}55;">{escape(label)}</span>')


def badge(status):
    """Pastille d'état (Normal / À surveiller / Action requise / Calibration)."""
    return _badge(status)


def all_clear(text):
    return f'<div class="ok">{escape(text)}</div>'
