"""Cartes d'actions expliquées : pourquoi l'alerte, que faire, quand escalader."""

ACTIONS = {
    "Cardiovasculaire": {
        "why": "Ta fréquence cardiaque au repos ou ta variabilité cardiaque s'écarte de ta normale personnelle. "
               "En microgravité, le système cardiovasculaire se reconditionne et peut vieillir plus vite.",
        "steps": [
            "Refais une mesure au calme, après 5 minutes de repos.",
            "Vérifie ton sommeil et ton niveau de stress des derniers jours.",
            "Si l'écart persiste, contacte l'équipe médicale.",
        ],
    },
    "Os et muscles": {
        "why": "Ta charge d'exercice ou ton poids s'écarte de ta normale : "
               "le risque de perte osseuse et de fonte musculaire augmente.",
        "steps": [
            "Ajuste ton protocole d'exercice : reprends la séance complète.",
            "Note les séances manquées et la raison.",
            "Si le poids continue de baisser, contacte l'équipe médicale.",
        ],
    },
    "Neuro-oculaire": {
        "why": "Ton acuité visuelle change, ce qui peut signaler une pression intracrânienne accrue (SANS).",
        "steps": [
            "Refais le test de vision dans de bonnes conditions de lumière.",
            "Signale tout changement de vision à l'équipe médicale rapidement.",
        ],
    },
    "Colonne vertébrale": {
        "why": "Ta douleur dorsale dépasse ta normale : la colonne s'allonge en microgravité, "
               "ce qui augmente le risque de hernie discale.",
        "steps": [
            "Fais tes exercices d'étirement et de renforcement du dos.",
            "Évite les charges soudaines et note la douleur chaque jour.",
            "Si la douleur augmente encore, contacte l'équipe médicale.",
        ],
    },
    "Sang et immunité": {
        "why": "Ta fatigue ou ton taux d'hémoglobine s'écarte de ta normale. "
               "L'anémie spatiale (baisse des globules rouges) et l'immunité affaiblie sont des risques connus.",
        "steps": [
            "Refais la mesure d'hémoglobine si possible.",
            "Hydrate-toi et vérifie ton sommeil.",
            "Note tes symptômes (gorge, peau, fièvre).",
            "Si la fatigue persiste, contacte l'équipe médicale.",
        ],
    },
    "Radiation": {
        "why": "Ton exposition aux radiations s'écarte de la normale.",
        "steps": [
            "Rejoins la zone la mieux protégée du vaisseau.",
            "Consulte les consignes de la mission pour les événements solaires.",
            "Signale l'exposition à l'équipe médicale.",
        ],
    },
    "Comportement": {
        "why": "Ton sommeil, ton humeur ou ton stress s'écarte de ta normale, ce qui affecte la vigilance.",
        "steps": [
            "Corrige ton sommeil : horaires réguliers, lumière vive réduite avant de dormir.",
            "Refais le questionnaire d'humeur dans quelques heures.",
            "Parles-en à un membre de l'équipage ou à l'équipe de soutien.",
        ],
    },
}

URGENCY = {"rouge": 2, "orange": 1}


def build_cards(details):
    """details : {domaine: {"status", "drivers", ...}} issu de detector.domain_details.

    Accepte aussi {domaine: état} (compatibilité). Retourne les cartes,
    les plus urgentes d'abord ; `drivers` liste [(indicateur, score)].
    """
    cards = []
    for domain, info in details.items():
        status = info["status"] if isinstance(info, dict) else info
        if status in URGENCY:
            drivers = info.get("drivers", []) if isinstance(info, dict) else []
            cards.append({"domain": domain, "status": status,
                          "drivers": drivers, **ACTIONS[domain]})
    return sorted(cards, key=lambda c: URGENCY[c["status"]], reverse=True)
