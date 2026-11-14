"""Accès prudent aux fichiers publics du NASA Open Science Data Repository.

Les données téléchargées restent en mémoire : ce module ne les ajoute pas à la
base des profils de BioSpace et ne les transforme pas en signes vitaux.

Diagnostic réseau (à lancer depuis la racine du projet) :
    python -m src.nasa_osdr            # étude OSD-575 par défaut
    python -m src.nasa_osdr 569
"""
from __future__ import annotations

import json
import re
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO
from zipfile import BadZipFile, ZipFile

import pandas as pd

BASE = "https://osdr.nasa.gov"
API = f"{BASE}/osdr/data/osd"
MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
MAX_JSON_BYTES = 32 * 1024 * 1024     # certaines métadonnées d'étude dépassent 8 Mo
ALLOWED_HOSTS = {"osdr.nasa.gov"}      # hôte de l'API et des liens retournés par l'API
TIMEOUT = 40
# UA de navigateur : certains pare-feu NASA refusent les agents inconnus (HTTP 403).
USER_AGENT = ("Mozilla/5.0 (compatible; BioSpace-NASA-OSDR-Viewer/1.1; "
              "+https://github.com/djohozinc-ship-it/NASA-Challenge)")


class OSDRError(RuntimeError):
    """Erreur de réseau, d'accès ou de format OSDR."""


def _host_allowed(host: str | None, *, redirect: bool = False) -> bool:
    """L'API et ses liens vivent sur osdr.nasa.gov ; les téléchargements peuvent être
    redirigés vers un autre serveur NASA (ex. stockage de fichiers) : on accepte alors
    n'importe quel sous-domaine de nasa.gov, toujours en HTTPS."""
    if not host:
        return False
    host = host.lower()
    if host in ALLOWED_HOSTS:
        return True
    return redirect and (host == "nasa.gov" or host.endswith(".nasa.gov"))


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    """Vérifie chaque redirection AVANT de l'exécuter (HTTPS et domaine NASA uniquement)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or not _host_allowed(parsed.hostname, redirect=True):
            raise OSDRError(f"Redirection refusée vers un serveur hors NASA : {parsed.hostname}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _ssl_context() -> ssl.SSLContext:
    """Contexte TLS avec les certificats de certifi quand il est disponible.

    Les exécutables PyInstaller et certains Python Windows/macOS n'ont pas de magasin de
    certificats système exploitable : sans certifi, l'erreur est CERTIFICATE_VERIFY_FAILED.
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:   # certifi absent : magasin système par défaut
        return ssl.create_default_context()


def _describe(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP {exc.code} {exc.reason}"
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, ssl.SSLCertVerificationError):
            return ("certificat TLS non reconnu (installez le paquet « certifi » ou mettez à jour "
                    f"les certificats du système) : {reason}")
        if isinstance(reason, socket.gaierror):
            return f"nom de domaine introuvable (DNS ou absence de connexion) : {reason}"
        return str(reason)
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return f"délai dépassé ({TIMEOUT} s)"
    return str(exc)


def _read_url(url: str, max_bytes: int = MAX_DOWNLOAD_BYTES) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not _host_allowed(parsed.hostname):
        raise OSDRError("URL de téléchargement non autorisée.")
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=_ssl_context()), _SafeRedirect())
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, text/plain, */*"})
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            final = urllib.parse.urlparse(response.geturl())
            if final.scheme != "https" or not _host_allowed(final.hostname, redirect=True):
                raise OSDRError("La redirection du téléchargement sort des serveurs NASA autorisés.")
            length = response.headers.get("Content-Length")
            if length and length.isdigit() and int(length) > max_bytes:
                raise OSDRError("Fichier trop volumineux pour l'aperçu intégré.")
            payload = response.read(max_bytes + 1)
    except OSDRError:
        raise
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OSDRError(f"Impossible de joindre NASA OSDR : {_describe(exc)}") from exc
    if len(payload) > max_bytes:
        raise OSDRError("Fichier trop volumineux pour l'aperçu intégré.")
    return payload


def _get_json(url: str):
    raw = _read_url(url, max_bytes=MAX_JSON_BYTES)
    try:
        return json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OSDRError("La réponse de l'API OSDR n'est pas un JSON exploitable.") from exc


def _study_id(value: str | int) -> str:
    match = re.fullmatch(r"(?:OSD-)?(\d+)", str(value).strip(), flags=re.IGNORECASE)
    if not match:
        raise ValueError("Identifiant invalide. Exemple attendu : OSD-575.")
    return match.group(1)


def study_metadata(study_id: str | int) -> dict:
    accession = _study_id(study_id)
    return _get_json(f"{API}/meta/{accession}")


def _file_records(node):
    """Parcourt les réponses API sans supposer un seul schéma de sérialisation."""
    if isinstance(node, dict):
        if node.get("remote_url"):
            yield node
        for value in node.values():
            yield from _file_records(value)
    elif isinstance(node, list):
        for value in node:
            yield from _file_records(value)


def _absolute_download_url(remote_url: str) -> str:
    url = urllib.parse.urljoin(BASE + "/", str(remote_url).strip())
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not _host_allowed(parsed.hostname):
        raise OSDRError("Le lien retourné par l'API ne pointe pas vers le serveur OSDR autorisé.")
    return url


def _files_urls(accession: str, page: int, size: int) -> list[str]:
    """La documentation NASA montre « /files/{id}/?page=… » ; on essaie aussi sans « / »."""
    query = f"page={page}&size={size}&all_files=false"
    return [f"{API}/files/{accession}/?{query}", f"{API}/files/{accession}?{query}"]


def study_files(study_id: str | int, page: int = 0, size: int = 25) -> list[dict]:
    accession = _study_id(study_id)
    size = max(1, min(int(size), 25))
    page = max(0, int(page))
    payload, last_error = None, None
    for url in _files_urls(accession, page, size):
        try:
            payload = _get_json(url)
            break
        except OSDRError as exc:
            last_error = exc
    if payload is None:
        raise last_error
    records = []
    seen = set()
    for item in _file_records(payload):
        remote = str(item["remote_url"])
        name = (item.get("file_name") or item.get("fileName") or item.get("filename")
                or item.get("name") or item.get("file") or remote.rsplit("/", 1)[-1])
        key = (str(name), remote)
        if key in seen:
            continue
        seen.add(key)
        try:
            download_url = _absolute_download_url(remote)
        except OSDRError:
            continue   # lien hors OSDR : ignoré plutôt que de faire échouer toute la liste
        records.append({
            "name": str(name),
            "remote_url": remote,
            "download_url": download_url,
            "size": item.get("file_size") or item.get("size") or item.get("fileSize"),
            "description": item.get("description") or "",
            "level": item.get("level") or item.get("data_level") or "",
        })
    return records


def _tabular_frame(payload: bytes, filename: str) -> pd.DataFrame:
    suffix = filename.lower().split("?")[0]
    separator = "\t" if suffix.endswith(".tsv") else None
    try:
        frame = pd.read_csv(BytesIO(payload), sep=separator, engine="python")
    except Exception as exc:
        raise OSDRError(f"Lecture du tableau impossible : {exc}") from exc
    if frame.empty:
        raise OSDRError("Le fichier ne contient aucune ligne de données.")
    return frame


def _table_members(archive: ZipFile) -> list[str]:
    """Tableaux raisonnablement petits d'une archive, sans chemin absolu ni « .. »."""
    members = []
    for item in archive.infolist():
        name = item.filename
        parts = name.replace("\\", "/").split("/")
        if (not item.is_dir()
                and name.lower().endswith((".csv", ".tsv", ".txt"))
                and item.file_size <= MAX_DOWNLOAD_BYTES
                and not name.startswith(("/", "\\"))
                and ".." not in parts):
            members.append(name)
    return members


def archive_members(file_record: dict) -> list[str]:
    """Liste les tableaux raisonnablement petits présents dans une archive ZIP publique."""
    payload = _read_url(file_record["download_url"])
    try:
        with ZipFile(BytesIO(payload)) as archive:
            return _table_members(archive)
    except BadZipFile as exc:
        raise OSDRError("L'archive téléchargée n'est pas un ZIP valide.") from exc


def download_table_file(file_record: dict, member: str | None = None) -> tuple[pd.DataFrame, str]:
    """Télécharge un petit fichier tabulaire public, éventuellement depuis un ZIP."""
    payload = _read_url(file_record["download_url"])
    name = str(file_record.get("name") or "dataset")
    suffix = name.lower().split("?")[0]

    if suffix.endswith(".zip"):
        try:
            with ZipFile(BytesIO(payload)) as archive:
                candidates = _table_members(archive)
                chosen = member or (candidates[0] if len(candidates) == 1 else None)
                if chosen not in candidates:
                    raise OSDRError("Sélectionnez un fichier tabulaire présent dans l'archive.")
                return _tabular_frame(archive.read(chosen), chosen), f"{name} · {chosen}"
        except BadZipFile as exc:
            raise OSDRError("L'archive téléchargée n'est pas un ZIP valide.") from exc

    if not suffix.endswith((".csv", ".tsv", ".txt")):
        raise OSDRError("Format non pris en charge pour l'aperçu. Formats acceptés : CSV, TSV, TXT ou ZIP.")
    return _tabular_frame(payload, name), name


def diagnose(study_id: str | int = 575) -> list[tuple[str, bool, str]]:
    """Teste la chaîne complète (DNS, TLS, métadonnées, fichiers) et dit où ça casse.

    Retourne une liste (étape, succès, détail). Ne lève jamais d'exception.
    """
    steps: list[tuple[str, bool, str]] = []

    def run(label, func):
        try:
            detail = func()
            steps.append((label, True, str(detail)))
            return True
        except Exception as exc:   # le but est justement de tout rapporter
            steps.append((label, False, f"{type(exc).__name__} : {exc}"))
            return False

    try:
        accession = _study_id(study_id)
    except ValueError as exc:
        return [("Identifiant", False, str(exc))]

    steps.append(("Environnement", True,
                  f"Python {sys.version.split()[0]} · {ssl.OPENSSL_VERSION}"))
    try:
        import certifi
        steps.append(("Certificats certifi", True, certifi.where()))
    except ImportError:
        steps.append(("Certificats certifi", False,
                      "paquet absent : pip install certifi (utile si erreur de certificat)"))

    if not run("Résolution DNS osdr.nasa.gov",
               lambda: socket.gethostbyname("osdr.nasa.gov")):
        return steps
    if not run(f"Métadonnées OSD-{accession}",
               lambda: f"{len(json.dumps(study_metadata(accession)))} caractères de JSON"):
        return steps

    def files_step():
        files = study_files(accession)
        if not files:
            raise OSDRError("réponse reçue mais aucun fichier avec « remote_url » reconnu")
        return f"{len(files)} fichier(s), ex. {files[0]['name']} → {files[0]['download_url']}"

    run(f"Liste des fichiers OSD-{accession}", files_step)
    return steps


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "575"
    results = diagnose(target)
    for label, ok, detail in results:
        print(f"[{'OK ' if ok else 'ÉCHEC'}] {label} : {detail}")
    sys.exit(0 if all(ok for _, ok, _ in results) else 1)
