# Sources de données NASA pour BioSpace

> Objectif : intégrer des observations biomédicales issues de recherches spatiales réelles, sans transformer des données de laboratoire en constantes physiologiques ni mélanger les cohortes.

## 1. Principes de sélection

1. Priorité aux données humaines issues d'astronautes ou d'équipages de missions spatiales.
2. Distinguer les astronautes professionnels des participants aux missions commerciales privées.
3. Conserver pour chaque observation : organisme, cohorte/mission, identifiant de l'étude, type d'échantillon, temps de prélèvement, unité, méthode, licence et DOI/source.
4. Ne jamais convertir une mesure biologique (par exemple une cytokine sérique) en fréquence cardiaque, SpO2 ou pression artérielle.
5. Les données synthétiques restent uniquement dans le mode démonstration et doivent être explicitement étiquetées.
6. Ne pas intégrer les données de rongeurs, de cultures cellulaires ou de tissus artificiels dans une vue présentée comme des mesures d'astronautes.

## 2. Données biologiques humaines : sources identifiées

### Inspiration4 — mission commerciale privée (2021)

Cette cohorte comprend quatre participants civils. Il s'agit d'une mission commerciale, et non d'une mission composée d'astronautes professionnels de la NASA.

| Accession | Contenu annoncé par NASA | Utilisation envisagée |
|---|---|---|
| OSD-569 | Sang total | Profil biologique / hématologie selon les fichiers publics disponibles |
| OSD-570 | Cellules mononucléées du sang périphérique (PBMC) | Immunologie cellulaire |
| OSD-571 | Plasma | Protéomique, métabolomique et autres profils plasmatiques |
| OSD-575 | Sérum : panel métabolique complet et cytokines immunitaires/cardiovasculaires | Analyse de biomarqueurs métaboliques, immunitaires et cardiovasculaires |
| OSD-656 | Urine | Biomarqueurs urinaires |
| OSD-687 | Cellules T | Analyse immunitaire |

**Étude prioritaire : OSD-575**

- Mission : Inspiration4, septembre 2021, vol de trois jours.
- Échantillons décrits : avant vol (L-92, L-44, L-3) et après vol (R+1, R+45, R+82).
- Mesures annoncées : panel métabolique complet et profils de cytokines immunitaires/cardiovasculaires.
- DOI : 10.26030/mc5d-p710.
- Licence affichée sur la fiche de l'étude : CC0-1.0.
- Fiche : https://osdr.nasa.gov/bio/repo/data/studies/OSD-575

**Limite temporelle à respecter :** la description publique d'OSD-575 énumère des prélèvements pré-vol et post-vol. Ne pas inventer de série continue ni présenter ces prélèvements comme des mesures quotidiennes en vol.

### Astronautes de missions spatiales : OSD-53

- Titre : *Spaceflight Modulates Gene Expression in Astronauts*.
- Cohorte décrite : six astronautes, vols spatiaux de courte durée.
- Matériel : sang total, avant et après le vol.
- Mesures : profils d'expression génique (microarray), pas des signes vitaux.
- DOI : 10.25966/qsf7-cr81.
- Fiche : https://osdr.nasa.gov/bio/repo/data/studies/OSD-53

### Autres données de recherche sur les astronautes

- OSD-484 : exosomes dérivés du plasma de trois astronautes, à L-10 et R+3 ; étude d'expression génique dans des cellules AC16 exposées à ces exosomes. Ce sont des résultats expérimentaux ex vivo, pas des mesures physiologiques directes des astronautes. DOI : 10.26030/semj-9y19. https://osdr.nasa.gov/bio/repo/data/studies/OSD-484
- OSD-343 : publication intégrative combinant plusieurs jeux de données GeneLab, des métriques humaines portant sur 59 astronautes et des données de la NASA Twins Study. À utiliser comme référence de recherche et non comme un fichier unique de constantes physiologiques. DOI : 10.26030/h968-2m75. https://osdr.nasa.gov/bio/repo/data/studies/OSD-343

## 3. Données physiologiques et comportementales : NASA Standard Measures

Le programme *Spaceflight Standard Measures* rassemble des mesures humaines répétées avant, pendant et après les missions. Les domaines annoncés par NASA comprennent notamment :

- actigraphie au poignet : activité et exposition à la lumière, utile pour l'étude veille-sommeil ;
- sommeil : questionnaires et mesures associées ;
- cognition et performance ;
- fonction sensorimotrice, équilibre et vestibulaire ;
- performance musculaire ;
- marqueurs biochimiques, profils cellulaires, microbiome ;
- mesures cardiovasculaires, notamment structure artérielle et réponses orthostatiques.

Une présentation NASA de 2023 indique que les données avaient été recueillies auprès de 31 membres d'équipage de l'ISS et archivées dans le NASA Life Sciences Data Archive / NASA Life Sciences Portal. L'accès aux données individuelles ou détaillées peut nécessiter une demande et une approbation ; il ne faut pas présumer que chaque fichier est ouvert au téléchargement.

- Description NASA : https://www.nasa.gov/reference/standard-measures/
- Portail NASA Life Sciences : https://nlsp.nasa.gov/
- Présentation NASA sur les mesures standard : https://ntrs.nasa.gov/citations/20230014025

**Plan d'accès :** inventorier les jeux de données publics et leurs variables dans NLSP/OSDR ; identifier les champs soumis à contrôle d'accès ; ne demander des données restreintes que par la procédure officielle. Les données publiques et autorisées doivent être dé-identifiées et utilisées conformément à leurs conditions.

## 4. API officielle et téléchargement

NASA documente une API publique OSDR :

- Fichiers d'une étude : https://osdr.nasa.gov/osdr/data/osd/files/{OSD_ID}
- Métadonnées d'une étude : https://osdr.nasa.gov/osdr/data/osd/meta/{OSD_ID}
- La réponse de l'API fichiers fournit les métadonnées des fichiers et leur emplacement de téléchargement HTTPS (remote_url).

Documentation : https://api.nasa.gov/ (section *Open Science Data Repository Public API*).

Le téléchargement et l'import devront :
- utiliser uniquement les fichiers publics ou pour lesquels l'accès a été accordé ;
- afficher la provenance et la licence ;
- conserver les fichiers originaux séparément des tables transformées ;
- enregistrer les versions, les dates d'accès, les unités et les règles de nettoyage ;
- refuser les fichiers dont le format ou le schéma n'a pas été reconnu ;
- ne jamais publier de données personnelles ou de fichiers bruts contrôlés.

## 5. Architecture cible dans BioSpace

Les données de recherche NASA ne doivent pas être injectées directement dans le modèle de surveillance quotidienne actuel. Ce dernier attend des séries journalières d'indicateurs comme FC, sommeil ou tension, alors que les jeux OSDR peuvent contenir des prélèvements ponctuels, des matrices de laboratoire, des profils d'expression génique et des variables spécifiques à une étude.

Prévoir deux espaces analytiques distincts :

1. **Physiologie et comportement** : actigraphie, sommeil, tests sensorimoteurs, activité, performance et variables cardiovasculaires réellement présentes dans les fichiers autorisés.
2. **Biologie et biomarqueurs** : sang, sérum, plasma, urine, cytokines, panels métaboliques, protéines, métabolites et données omiques.

Pour chaque graphique, afficher la cohorte, la mission, l'étude OSD, la matrice, le temps de collecte et l'unité. Les comparaisons pré-vol / en vol / post-vol ne seront disponibles que si les fichiers contiennent réellement ces temps de collecte.

## 6. Limites scientifiques et de confidentialité

- Les données publiques OSDR d'origine humaine sont parfois des données traitées et dé-identifiées ; certaines données brutes, notamment les séquences génétiques, sont contrôlées.
- Les participants d'Inspiration4 sont des civils ayant participé à une mission commerciale.
- Les données OSD-575 sont des biomarqueurs sanguins, pas des mesures continues de FC, SpO2 ou tension artérielle.
- Les mesures standard NASA ne sont pas toutes nécessairement publiques ; les accès soumis à approbation ne doivent pas être contournés.
- BioSpace est un outil de visualisation et d'analyse de recherche ; ses résultats ne constituent pas un diagnostic ni une décision médicale.