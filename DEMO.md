# Guide de démonstration et de pitch (3 minutes)

## Message central

> En mission longue, l'astronaute doit repérer seul ses propres changements de santé.
> BioSpace apprend sa normale, détecte l'écart, explique quoi faire, suit l'action
> et prévient l'équipe médicale si rien n'est fait. Le tout sans connexion.

## Préparation (2 minutes avant)

1. `python launcher.py`, puis ouvre l'application.
2. Barre latérale > **Nouveau profil** : nom « Cdt Démo », type **Démonstration**,
   scénario **Épisode infectieux**. Crée-le. L'application s'ouvre au jour 125.
3. Crée un deuxième profil de démonstration **Dérive cardiovasculaire** pour la fin.
4. Garde un profil réel vide (« Cdt Réel ») pour montrer la saisie.

## Déroulé

| Temps | Action à l'écran | À dire |
|---|---|---|
| 0:00 | Page d'accueil, badge **Mode autonome** | « Sur Mars, pas de liaison temps réel. Tout tourne à bord, sans réseau. » |
| 0:20 | Profil Épisode infectieux : bandeau **rouge**, radar, alerte « Sang et immunité » | « Il est comparé à sa propre normale : température, symptômes, fatigue. Pas à une norme générale. » |
| 0:45 | Onglet **Actions** : carte expliquée, indicateurs en cause | « Chaque alerte dit pourquoi, quel indicateur, et quoi faire. » |
| 1:05 | Barre latérale **+1 j** : toast **Escalade automatique** | « Sans action sous 24 h, l'alerte remonte à l'équipe médicale. L'astronaute n'a pas à y penser. » |
| 1:20 | Cliquer **Signaler à l'équipe médicale** avec une note | « L'action est tracée dans le journal. » |
| 1:35 | **+3 j** (orange), puis **+14 j** : alerte résolue | « Quand il est revenu à la normale 3 jours de suite, l'alerte se ferme. Pas de clignotement. » |
| 1:50 | Profil **Cdt Réel** > **Bilan du jour** : tension 170 > Enregistrer | « Une valeur dangereuse passe en rouge tout de suite, même avant la fin de la calibration. » |
| 2:15 | Onglet **Rapport** > Générer le PDF, l'ouvrir | « Prêt à transmettre quand la liaison revient : état, alertes, tendances, journal. » |
| 2:35 | Onglet **Validation** | « Mesuré sur 40 missions simulées : 4,5 % de jours en alerte sur une mission normale, 0,02 % en rouge, 7 scénarios sur 7 détectés. » |
| 2:55 | Retour vue d'ensemble | « BioSpace : l'astronaute reste acteur de sa santé, même seul. » |

Plan B si le temps est court : sauter le profil réel et ouvrir directement le rapport.

## Questions probables du jury

**Les données sont-elles réelles ?** Non : synthétiques, pour la démonstration. Le logiciel accepte la saisie
quotidienne et l'import CSV, donc il est prêt pour de vraies mesures.

**Comment avez-vous choisi les seuils ?** Ils sont illustratifs. Le taux de fausses alertes et les délais sont
mesurés dans l'onglet Validation, et les seuils se règlent dans un seul fichier. Une validation clinique serait
la prochaine étape.

**Pourquoi comparer à soi-même ?** La physiologie varie beaucoup d'une personne à l'autre, et en vol elle dérive.
Un écart par rapport à sa propre normale est plus informatif qu'une norme de population.

**Et si la calibration est faussée par un mauvais début de mission ?** C'est une limite connue : la référence
est fixe sur 30 jours. Une baseline adaptative, validée par un médecin, est une piste. Les seuils critiques
absolus protègent déjà pendant et après la calibration.

**Qu'est-ce qui n'est pas couvert ?** Capteurs réels, diagnostic, synchronisation chiffrée avec le sol, multi-équipage.

**Pourquoi hors ligne ?** Latence et coupures de liaison sur Mars : le suivi ne doit jamais dépendre du sol.

## À vérifier avant de soumettre

- Les exigences exactes de soumission du défi (format, vidéo, lien) sur la page de l'événement.
- Un lancement à froid sur la machine de démonstration (`python -m pytest` puis `python launcher.py`).
- Une capture d'écran de chaque onglet pour le dossier de présentation.
