# BioSpace — Logiciel de suivi de santé pour astronautes

Réponse au défi **NASA Space Apps 2026 : « Créer un logiciel de surveillance de la santé pour les
astronautes en mission spatiale »**.

Lors des longues missions, l'astronaute porte lui-même une grande part de la responsabilité de repérer
ses propres changements de santé. BioSpace rassemble ses indicateurs, apprend **sa** normale, détecte les
écarts par système physiologique, explique chaque alerte, suit les actions entreprises et prépare un
rapport pour l'équipe médicale. Tout fonctionne **hors ligne**.

> Données synthétiques ou auto-déclarées, seuils illustratifs. Ne remplace pas un avis médical.

## Fonctionnalités

| | |
|---|---|
| **Baseline personnelle** | Chaque astronaute est comparé à lui-même (calibration sur 30 jours), pas à une norme. |
| **16 indicateurs, 7 systèmes** | Cardiovasculaire, os et muscles, neuro-oculaire, colonne, sang et immunité, radiation, comportement. |
| **Bilan du jour** | Saisie guidée en une minute, validée (bornes plausibles), bilans partiels acceptés. |
| **Import CSV** | Validation ligne par ligne, rapport des rejets, virgule décimale acceptée. |
| **Seuils critiques absolus** | Une valeur dangereuse passe le système en rouge immédiatement, même pendant la calibration. |
| **Cartes d'action expliquées** | Pourquoi l'alerte, quel indicateur est en cause, que faire. |
| **Boucle d'action suivie** | À faire, fait, reporté, signalé. Escalade automatique vers l'équipe médicale sans action. |
| **Rapport médical** | PDF (état, alertes, indicateurs, tendances, journal) et CSV, générés localement. |
| **Persistance locale** | Base SQLite, profils multiples, journal des événements, sauvegarde en un clic. |
| **Mode autonome** | Aucun appel réseau, aucune ressource externe, aucune liaison sol requise. |
| **Validation mesurée** | Page dédiée : fausses alertes et délais de détection sur des centaines de missions simulées. |

## Démarrage rapide

```bash
pip install -r requirements.txt
python launcher.py          # ouvre le navigateur ; ou : streamlit run app.py
```

Aucune étape de génération de données : au premier lancement, crée un profil dans la barre latérale.
Choisis **Démonstration** pour un scénario simulé, ou **Profil réel** pour saisir et importer tes données.

Scripts équivalents : `lancer_biospace.sh` (Linux, macOS) et `lancer_biospace.bat` (Windows).

### Exécutable autonome

```bash
pip install pyinstaller
python build_exe.py         # produit dist/BioSpace/BioSpace
```

L'exécutable embarque Python et toutes les dépendances. Il range ses données dans le dossier utilisateur
(`~/.local/share/BioSpace`, `%APPDATA%\BioSpace`, `~/Library/Application Support/BioSpace`).
Il se construit pour le système sur lequel on lance le script. Vérifié ici sur Linux (taille : environ 530 Mo).

## Indicateurs

| Système | Indicateurs | Seuil critique absolu |
|---|---|---|
| Cardiovasculaire | Fréquence cardiaque au repos, variabilité cardiaque (RMSSD), tension systolique | FC < 40 ou > 130 bpm ; tension > 160 mmHg |
| Os et muscles | Activité physique, poids | |
| Neuro-oculaire | Acuité visuelle (risque SANS) | acuité < 0,6 |
| Colonne vertébrale | Douleur dorsale | |
| Sang et immunité | Fatigue, hémoglobine (proxy des globules rouges), température, symptômes | hémoglobine < 10 g/dL ; température > 38,5 °C |
| Radiation | Débit de dose (dose cumulée affichée) | débit > 5 mSv/j |
| Comportement | Sommeil, humeur, stress, contacts sociaux | sommeil < 3 h |

Les seuils et unités sont définis dans `src/config.py`, un seul endroit à modifier.

## Méthode

1. **Calibration** : les 30 premiers jours fixent moyenne et écart-type de chaque indicateur.
2. **Lissage** : moyenne glissante sur 7 jours, mesures manquantes tolérées.
3. **Écart** : z-score normalisé par `σ · √(1/n + 1/n_réf)` (bruit de la moyenne et incertitude de la
   référence), orienté selon le sens dangereux de chaque indicateur.
4. **Persistance** : l'écart doit durer 3 jours consécutifs.
5. **Système** : état de son indicateur le plus préoccupant. Orange dès 2,5, rouge dès 4,0.
6. **Suivi** : une alerte est escaladée sans action après 1 jour (rouge) ou 3 jours (orange), et close
   après 3 jours consécutifs sous le seuil, mesurés sur les données.

## Résultats de validation

Mesurés sur 40 missions simulées par scénario (graines distinctes de la démonstration), 144 jours
évalués par mission après calibration. Reproductibles dans l'onglet **Validation**.

- Mission nominale : **4,9 % des jours** avec au moins un système orange ou rouge, **0,02 %** en rouge.
  Avec 10 % de mesures manquantes : 5,1 % et 0,02 %.
- **7 scénarios d'anomalie sur 7 détectés dans 100 % des missions.**

| Scénario | Système | Délai médian de détection |
|---|---|---|
| Éruption solaire (pic de 3 jours) | Radiation | 2 jours |
| Épisode infectieux | Sang et immunité | 3 jours |
| Dérive cardiovasculaire | Cardiovasculaire | 16 jours |
| Déconditionnement | Os et muscles | 20 jours |
| Risque neuro-oculaire (SANS) | Neuro-oculaire | 26 jours |
| Dégradation sommeil et stress | Comportement | 31 jours |
| Isolement et confinement | Comportement | 34 jours |

Les dérives simulées sont lentes (150 jours) : un délai de 30 jours correspond à un écart encore faible.
Les seuils critiques absolus ne sont pas inclus dans ces mesures.

## Organisation

```
app.py                  Interface (Streamlit) : profils, onglets
launcher.py             Lanceur local (port libre, navigateur, dossier de données)
build_exe.py            Construction de l'exécutable (PyInstaller)
src/config.py           Indicateurs, domaines, bornes, seuils critiques
src/generator.py        Données synthétiques et 8 scénarios
src/detector.py         Baseline, z-scores, persistance, seuils critiques
src/storage.py          Base SQLite : profils, mesures, journal, actions
src/ingest.py           Saisie et import CSV validés
src/tracker.py          Alertes, actions suivies, escalade automatique
src/report.py           Rapport PDF et exports CSV
src/validation.py       Mesure des fausses alertes et délais de détection
src/summary.py          Calculs de synthèse partagés
src/demo.py             Mode démonstration
src/applog.py           Journalisation locale
src/actions.py          Conseils par système
src/ui.py               Éléments visuels (HTML/CSS hors ligne)
src/views/              Une vue par onglet
tests/                  67 tests automatisés
```

Tests : `python -m pytest`

## Format d'import CSV

Colonne `date` (AAAA-MM-JJ) puis une colonne par indicateur de `src/config.py` (le modèle est téléchargeable
dans l'onglet *Bilan du jour*). Séparateur virgule ou point-virgule. Les colonnes inconnues sont ignorées,
les valeurs hors bornes plausibles sont rejetées et listées, sans jamais bloquer l'application.

## Données et confidentialité

Tout reste sur l'ordinateur : base `data/biospace.db` (ou dossier utilisateur pour l'exécutable) et journal
`biospace.log`. Aucune télémétrie (`gatherUsageStats` désactivé), aucune requête externe.

## Limites

Seuils illustratifs, sans validation clinique ; référence fixe de 30 jours ; données synthétiques pour la
démonstration ; conseils généraux non médicaux ; hémoglobine et symptômes sont des proxys ou des
auto-déclarations. Pistes : baseline adaptative validée par un médecin, capteurs réels, synchronisation
chiffrée avec le sol au retour de la liaison, multi-équipage.
