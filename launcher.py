"""Lanceur BioSpace : démarre l'application en local et ouvre le navigateur.

Usage :
    python launcher.py                  # depuis les sources
    BioSpace (exécutable)               # après build_exe.py

Les données (base SQLite, journal) sont rangées dans le dossier utilisateur
quand l'application est empaquetée, ou dans ./data/ depuis les sources.
Option : --no-browser, --port N, --data-dir CHEMIN.
"""
import argparse
import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path


def base_dir():
    """Dossier contenant app.py et src/ (différent dans un exécutable PyInstaller)."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def user_data_dir():
    if sys.platform.startswith("win"):
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "BioSpace"


def free_port(preferred=8501):
    for port in list(range(preferred, preferred + 20)) + [0]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return s.getsockname()[1]
            except OSError:
                continue
    raise RuntimeError("Aucun port local disponible.")


def main(argv=None):
    parser = argparse.ArgumentParser(description="BioSpace, suivi de santé des astronautes")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--data-dir", type=Path, default=None)
    args = parser.parse_args(argv)

    frozen = getattr(sys, "frozen", False)
    data_dir = args.data_dir or (user_data_dir() if frozen else None)
    if data_dir:
        data_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("BIOSPACE_DB", str(data_dir / "biospace.db"))
        os.environ.setdefault("BIOSPACE_LOG", str(data_dir / "biospace.log"))

    root = base_dir()
    os.chdir(root)
    sys.path.insert(0, str(root))
    port = args.port or free_port()
    url = f"http://localhost:{port}"
    print(f"BioSpace démarre sur {url}  (Ctrl+C pour quitter)", flush=True)
    if os.environ.get("BIOSPACE_DB"):
        print(f"Données : {os.environ['BIOSPACE_DB']}", flush=True)
    if not args.no_browser:
        threading.Timer(2.5, lambda: webbrowser.open(url)).start()

    from streamlit.web import cli as stcli
    sys.argv = [
        "streamlit", "run", str(root / "app.py"),
        "--server.port", str(port), "--server.headless", "true",
        "--server.address", "127.0.0.1",
        "--browser.gatherUsageStats", "false", "--global.developmentMode", "false",
        "--theme.base", "dark", "--theme.primaryColor", "#4F8BF9",
        "--theme.backgroundColor", "#0B1220", "--theme.secondaryBackgroundColor", "#101A2D",
        "--theme.textColor", "#EAF0FA",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
