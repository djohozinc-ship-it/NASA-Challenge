# Références scientifiques et ressources

Ce document recense les ressources utilisées pour orienter le développement de BioSpace et l'exploration des données spatiales. Les fiches OSDR restent les références prioritaires pour vérifier la version, les fichiers, les variables, la cohorte et les conditions de réutilisation de chaque jeu de données.

## 1. NASA Open Science Data Repository (OSDR)

1. **NASA Open Science Data Repository — portail de données.**  
   https://osdr.nasa.gov/bio/repo/

2. **NASA OSDR Public API — documentation officielle.** Décrit les API de recherche, de métadonnées et de fichiers, ainsi que les champs `remote_url`.  
   https://api.nasa.gov/ (rubrique *Open Science Data Repository Public API*)

3. **NASA OSDR FAQ.** Accès aux données, formats, citation du dépôt et distinction entre données traitées publiques et séquences contrôlées.  
   https://science.nasa.gov/reference/osdr-faq/

4. **Gebre, S. G., Scott, R. T., Saravia-Butler, A. M., Lopez, D. K., Sanders, L. M. & Costes, S. V. (2024).** *NASA Open Science Data Repository: Open Science for Life in Space.* Nucleic Acids Research.  
   DOI : https://doi.org/10.1093/nar/gkae1116

## 2. Études humaines et données Inspiration4

5. **Sanders, L. M. et al. (2024).** *Inspiration4 data access through the NASA Open Science Data Repository.* npj Microgravity, 10, 56. Présente les jeux de données Inspiration4 et leur organisation par type d'échantillon.  
   DOI : https://doi.org/10.1038/s41526-024-00393-5

6. **NASA OSDR — OSD-575 : Inspiration4 blood serum.** Panel métabolique et mesures de cytokines sur des échantillons de sérum. Vérifier les temps de prélèvement et les fichiers de chaque version avant toute analyse.  
   https://osdr.nasa.gov/bio/repo/data/studies/OSD-575

7. **NASA OSDR — OSD-569 : whole blood.**  
   https://osdr.nasa.gov/bio/repo/data/studies/OSD-569

8. **NASA OSDR — OSD-570 : peripheral blood mononuclear cells (PBMC).**  
   https://osdr.nasa.gov/bio/repo/data/studies/OSD-570

9. **NASA OSDR — OSD-571 : blood plasma.**  
   https://osdr.nasa.gov/bio/repo/data/studies/OSD-571

10. **NASA OSDR — OSD-656 : urine.**  
    https://osdr.nasa.gov/bio/repo/data/studies/OSD-656

11. **NASA OSDR — OSD-687 : T cells.**  
    https://osdr.nasa.gov/bio/repo/data/studies/OSD-687

## 3. Autres études d'astronautes

12. **NASA OSDR — OSD-53 : Spaceflight Modulates Gene Expression in Astronauts.** Profils d'expression génique sur des échantillons sanguins avant et après vol ; ce ne sont pas des signes vitaux.  
    DOI : https://doi.org/10.25966/qsf7-cr81  
    Fiche : https://osdr.nasa.gov/bio/repo/data/studies/OSD-53

13. **NASA OSDR — OSD-484 : plasma-derived exosomes.** Étude portant sur des exosomes plasmatiques et des expériences cellulaires ex vivo ; ne pas interpréter les résultats cellulaires comme des mesures physiologiques directes des astronautes.  
    DOI : https://doi.org/10.26030/semj-9y19  
    Fiche : https://osdr.nasa.gov/bio/repo/data/studies/OSD-484

14. **NASA OSDR — OSD-343.** Ressource intégrative à consulter pour ses liens avec les données d'astronautes et la NASA Twins Study. Son contenu ne constitue pas un fichier unique de constantes physiologiques.  
    DOI : https://doi.org/10.26030/h968-2m75  
    Fiche : https://osdr.nasa.gov/bio/repo/data/studies/OSD-343

## 4. Physiologie, comportement et mesures standard NASA

15. **NASA — Spaceflight Standard Measures.** Présentation des domaines de mesures humaines suivis dans le cadre des missions spatiales.  
    https://www.nasa.gov/reference/standard-measures/

16. **NASA Life Sciences Portal (NLSP).** Portail de recherche et d'accès aux données des sciences de la vie spatiales ; certains jeux ou fichiers peuvent nécessiter une autorisation.  
    https://nlsp.nasa.gov/

17. **NASA Technical Reports Server — Standard Measures (2023).**  
    https://ntrs.nasa.gov/citations/20230014025

## 5. Principes d'utilisation dans BioSpace

- Les données de laboratoire (sérum, plasma, sang, cytokines, métabolites, expression génique) sont analysées séparément des séries physiologiques (fréquence cardiaque, sommeil, actigraphie, tension, etc.).
- Une variable ne doit être utilisée qu'après vérification de sa définition, de son unité, de sa méthode, de sa population et de son temps de collecte dans les métadonnées de l'étude.
- Les données synthétiques servent uniquement aux démonstrations et aux tests ; elles ne sont pas présentées comme des observations NASA.
- La disponibilité sur OSDR ne signifie pas que tous les fichiers sont libres de toute restriction. La licence et les conditions affichées pour la version exacte du jeu de données doivent être vérifiées avant redistribution.
- Les références scientifiques ne constituent pas une validation clinique du logiciel. BioSpace est un prototype de suivi et de visualisation, pas un dispositif médical certifié ni un outil de diagnostic.

**Date de consultation du dépôt et des liens : 13 novembre 2026.** Les fiches OSDR et leurs fichiers peuvent évoluer ; enregistrer l'accession et la version effectivement utilisées dans toute analyse reproductible.
