"""Rapports pour l'équipe médicale : PDF (lisible) et CSV (exploitable).

Aucune dépendance réseau. Le PDF utilise les polices standard (Latin-1) : les
caractères hors Latin-1 sont remplacés.
"""
import io
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from src.config import DOMAINS, LABELS, UNITS
from src.detector import BASELINE_DAYS, WINDOW
from src.summary import domain_rows, indicator_rows, mission_summary, with_unit
from src.tracker import STATES, days_open

STATUS_FR = {"vert": "Normal", "orange": "À surveiller", "rouge": "Action requise",
             "inconnu": "Calibration"}
STATUS_COLOR = {"vert": "#2ECC71", "orange": "#F39C12", "rouge": "#E5484D", "inconnu": "#7F8C9B"}
EVENT_FR = {
    "alerte_ouverte": "Alerte ouverte", "alerte_aggravee": "Alerte aggravée", "alerte_attenuee": "Alerte atténuée",
    "alerte_resolue": "Alerte résolue", "escalade_auto": "Escalade automatique",
    "action_fait": "Action effectuée", "action_reporte": "Action reportée",
    "action_signale": "Signalé à l'équipe médicale",
}
NAVY = colors.HexColor("#0B1220")
GREY = colors.HexColor("#5B6B85")
LINE = colors.HexColor("#D5DCE8")


def _t(text):
    """Texte compatible polices standard (Latin-1) et échappé pour Paragraph."""
    text = (str(text).replace("→", "->").replace("≥", ">=").replace("≤", "<=")
            .replace("σ", "sigma").replace("‑", "-").replace(" ", " "))
    text = text.encode("cp1252", errors="replace").decode("cp1252")
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], fontName="Helvetica-Bold",
                                fontSize=19, textColor=NAVY, alignment=0, spaceAfter=2),
        "sub": ParagraphStyle("s", parent=base["Normal"], fontSize=9, textColor=GREY, spaceAfter=10),
        "h": ParagraphStyle("h", parent=base["Heading2"], fontName="Helvetica-Bold",
                            fontSize=12, textColor=NAVY, spaceBefore=12, spaceAfter=6),
        "p": ParagraphStyle("p", parent=base["Normal"], fontSize=9, leading=12),
        "small": ParagraphStyle("sm", parent=base["Normal"], fontSize=7.5, leading=10, textColor=GREY),
        "cell": ParagraphStyle("c", parent=base["Normal"], fontSize=8, leading=10),
        "cellb": ParagraphStyle("cb", parent=base["Normal"], fontName="Helvetica-Bold",
                                fontSize=8, leading=10),
    }


def _table(data, widths, status_col=None, statuses=None):
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FB")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if status_col is not None and statuses:
        for r, s in enumerate(statuses, start=1):
            style += [("BACKGROUND", (status_col, r), (status_col, r), colors.HexColor(STATUS_COLOR[s])),
                      ("TEXTCOLOR", (status_col, r), (status_col, r), colors.white),
                      ("FONTNAME", (status_col, r), (status_col, r), "Helvetica-Bold")]
    t.setStyle(TableStyle(style))
    return t


def _trend_figure(df, indicators):
    """Petites courbes des indicateurs les plus préoccupants (PNG en mémoire)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None
    indicators = indicators[:4]
    if not indicators or len(df) < BASELINE_DAYS:
        return None
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 3.9), dpi=170)
    for ax, c in zip(axes.flat, indicators):
        base = df.iloc[:BASELINE_DAYS][c]
        mean, std = base.mean(), base.std()
        ax.axhspan(mean - 2.5 * std, mean + 2.5 * std, color="#2ECC71", alpha=0.12, lw=0)
        ax.plot(df["date"], df[c], color="#A9B7CF", lw=0.7)
        ax.plot(df["date"], df[c].rolling(WINDOW, min_periods=4).mean(), color="#2B6BE0", lw=1.8)
        ax.set_title(LABELS[c] + (f" ({UNITS[c]})" if UNITS[c] else ""), fontsize=7.5, loc="left")
        ax.tick_params(labelsize=6)
        ax.spines[["top", "right"]].set_visible(False)
        ax.margins(x=0.01)
        for lab in ax.get_xticklabels():
            lab.set_rotation(0)
        ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator())
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%m/%y"))
    for ax in list(axes.flat)[len(indicators):]:
        ax.axis("off")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf


def build_pdf(astronaut, df, z, details, items, events, as_of):
    """Génère le rapport PDF. Retourne les octets du fichier."""
    st = _styles()
    buf = io.BytesIO()
    as_of = pd.Timestamp(as_of)
    day = (as_of - df["date"].iloc[0]).days + 1 if len(df) else 0

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GREY)
        canvas.drawString(18 * mm, 10 * mm,
                          _t("BioSpace - données synthétiques ou auto-déclarées, ne remplace pas un avis médical."))
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=18 * mm,
                            title="Rapport de santé BioSpace", author="BioSpace")
    s = []
    s.append(Paragraph(_t("Rapport de santé pour l'équipe médicale"), st["title"]))
    s.append(Paragraph(_t(
        f"Astronaute : <b>{astronaut['name']}</b> &nbsp;|&nbsp; Jour de mission : {day} "
        f"&nbsp;|&nbsp; Données jusqu'au {as_of:%d/%m/%Y} &nbsp;|&nbsp; "
        f"Édité le {datetime.now():%d/%m/%Y %H:%M}").replace("&amp;nbsp;", "&nbsp;")
        .replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>"), st["sub"]))

    summ = mission_summary(details)
    headline = (f"{summ['rouge']} domaine(s) en action requise, {summ['orange']} à surveiller, "
                f"{summ['vert']} normaux" + (f", {summ['inconnu']} en calibration" if summ["inconnu"] else ""))
    s.append(Paragraph(_t("Synthèse : " + headline), st["p"]))

    # 1. Domaines
    s.append(Paragraph(_t("1. État par système physiologique"), st["h"]))
    rows = domain_rows(details)
    data = [["Système", "État", "Indicateur en cause", "Score"]]
    for r in rows:
        driver = LABELS[r["driver"]] if r["driver"] else "-"
        if r["critical"]:
            driver += " (seuil critique)"
        score = "-" if pd.isna(r["score"]) else f"{max(0.0, r['score']):.1f}"
        data.append([Paragraph(_t(r["domain"]), st["cellb"]), STATUS_FR[r["status"]],
                     Paragraph(_t(driver), st["cell"]), score])
    s.append(_table(data, [44 * mm, 30 * mm, 80 * mm, 20 * mm], 1, [r["status"] for r in rows]))
    s.append(Paragraph(_t(f"Score de danger : écart à la référence personnelle, orange à partir de 2,5, "
                          f"rouge à partir de 4,0 (moyenne {WINDOW} jours, référence {BASELINE_DAYS} jours)."),
                       st["small"]))

    # 2. Alertes
    s.append(Paragraph(_t("2. Alertes en cours et actions"), st["h"]))
    current = [i for i in items if i["state"] != "resolue"]
    if not current:
        s.append(Paragraph(_t("Aucune alerte en cours."), st["p"]))
    else:
        data = [["Système", "Gravité", "Ouverte le", "Jours", "Statut de l'action"]]
        for i in current:
            data.append([Paragraph(_t(i["domain"]), st["cellb"]), STATUS_FR[i["status"]],
                         pd.Timestamp(i["opened"]).strftime("%d/%m/%Y"), str(days_open(i, as_of)),
                         Paragraph(_t(STATES[i["state"]] + (f" - {i['note']}" if i.get("note") else "")),
                                   st["cell"])])
        s.append(_table(data, [44 * mm, 28 * mm, 26 * mm, 14 * mm, 62 * mm], 1,
                        [i["status"] for i in current]))

    # 3. Indicateurs
    s.append(Paragraph(_t("3. Indicateurs : valeur récente et référence personnelle"), st["h"]))
    irows = indicator_rows(df, z)
    data = [["Indicateur", f"Moyenne {WINDOW} j", "Référence", "Écart", "État"]]
    for r in irows:
        delta = ("-" if r["delta_pct"] is None else
                 "0 %" if round(r["delta_pct"]) == 0 else f"{r['delta_pct']:+.0f} %")
        data.append([Paragraph(_t(r["label"]), st["cell"]), with_unit(r["value"], r["indicator"]),
                     with_unit(r["reference"], r["indicator"]), delta, STATUS_FR[r["status"]]])
    s.append(_table(data, [66 * mm, 28 * mm, 28 * mm, 18 * mm, 30 * mm], 4,
                    [r["status"] for r in irows]))

    # 4. Tendances
    ranked = sorted([r for r in irows if not pd.isna(r["score"])], key=lambda r: r["score"], reverse=True)
    fig = _trend_figure(df, [r["indicator"] for r in ranked])
    if fig is not None:
        s.append(KeepTogether([
            Paragraph(_t("4. Tendances des indicateurs les plus écartés"), st["h"]),
            Image(fig, width=170 * mm, height=170 * mm * 3.9 / 7.4),
            Paragraph(_t("Gris : mesure quotidienne. Bleu : moyenne 7 jours. "
                         "Zone verte : plage normale personnelle."), st["small"]),
        ]))

    # 5. Journal
    s.append(Paragraph(_t("5. Journal des événements récents"), st["h"]))
    if not events:
        s.append(Paragraph(_t("Aucun événement enregistré."), st["p"]))
    else:
        data = [["Date", "Événement", "Système", "Détail"]]
        for e in events[:25]:
            data.append([pd.Timestamp(e["date"]).strftime("%d/%m/%Y"),
                         Paragraph(_t(EVENT_FR.get(e["kind"], e["kind"])), st["cell"]),
                         Paragraph(_t(e["domain"] or "-"), st["cell"]),
                         Paragraph(_t(e["detail"] or ""), st["cell"])])
        s.append(_table(data, [22 * mm, 40 * mm, 38 * mm, 74 * mm]))

    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


def measurements_csv(df):
    """CSV des mesures quotidiennes (utf-8 avec BOM, ouvrable dans Excel)."""
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out.to_csv(index=False).encode("utf-8-sig")


def events_csv(events):
    cols = ["date", "kind", "domain", "status", "detail"]
    return pd.DataFrame(events, columns=cols if events else cols).to_csv(index=False).encode("utf-8-sig")
