"""Construit un exécutable autonome BioSpace avec PyInstaller.

    pip install pyinstaller
    python build_exe.py

Résultat : dist/BioSpace/ (dossier) avec l'exécutable BioSpace (ou BioSpace.exe).
L'exécutable se construit pour le système sur lequel on lance ce script
(Windows, macOS ou Linux) : il faut donc le lancer sur chaque système cible.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEP = ";" if sys.platform.startswith("win") else ":"


def main():
    cmd = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
        "--name", "BioSpace", "--console",
        "--collect-all", "streamlit", "--copy-metadata", "streamlit",
        "--collect-submodules", "uvicorn", "--collect-submodules", "starlette",
        "--collect-all", "plotly", "--collect-all", "reportlab",
        "--collect-data", "certifi",   # certificats TLS pour l'API NASA OSDR
        "--hidden-import", "matplotlib.backends.backend_agg",
        "--add-data", f"{ROOT / 'app.py'}{SEP}.",
        "--add-data", f"{ROOT / 'src'}{SEP}src",
        "--add-data", f"{ROOT / '.streamlit'}{SEP}.streamlit",
        str(ROOT / "launcher.py"),
    ]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)
    print("\nTerminé : dist/BioSpace/BioSpace")


if __name__ == "__main__":
    main()
