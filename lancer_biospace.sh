#!/usr/bin/env bash
# Lance BioSpace depuis les sources (Linux / macOS). Rendre exécutable : chmod +x lancer_biospace.sh
cd "$(dirname "$0")"
python3 launcher.py "$@"
