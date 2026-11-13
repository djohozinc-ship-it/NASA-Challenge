"""Accès prudent aux fichiers publics du NASA Open Science Data Repository.

Les données téléchargées restent en mémoire : ce module ne les ajoute pas à la
base des profils de BioSpace et ne les transforme pas en signes vitaux.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO
from zipfile import BadZipFile, ZipFile

import pandas as pd

BASE = "https://osdr.nasa.gov"
API = f"{BASE}/osdr/data/osd"
MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_HOSTS = {"osdr.nasa.gov"}


class OSDRError(RuntimeError):
    """Erreur de réseau, d'accès ou de format OSDR."""


def _read_url(url: str, max_bytes: int = MAX_DOWNLOAD_BYTES) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise OSDRError("URL de téléchargement non autorisée.")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "BioSpace-NASA-OSDR-Viewer/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > max_bytes:
                raise OSDRError("Fichier trop volumineux pour l'aperçu intégré.")
            payload = response.read(max_bytes + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OSDRError(f"Impossible de joindre NASA OSDR : {exc}") from exc
    if len(payload) > max_bytes:
        raise OSDRError("Fichier trop volumineux pour l'aperçu intégré.")
    return payload


def _get_json(url: str) -> dict:
    raw = _read_url(url, max_bytes=8 * 1024 * 1024)
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
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise OSDRError("Le lien retourné par l'API ne pointe pas vers le serveur OSDR autorisé.")
    return url


def study_files(study_id: str | int, page: int = 0, size: int = 25) -> list[dict]:
    accession = _study_id(study_id)
    size = max(1, min(int(size), 25))
    page = max(0, int(page))
    url = f"{API}/files/{accession}?page={page}&size={size}&all_files=false"
    payload = _get_json(url)
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
        records.append({
            "name": str(name),
            "remote_url": remote,
            "download_url": _absolute_download_url(remote),
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


def archive_members(file_record: dict) -> list[str]:
    """Liste les tableaux raisonnablement petits présents dans une archive ZIP publique."""
    payload = _read_url(file_record["download_url"])
    try:
        with ZipFile(BytesIO(payload)) as archive:
            return [
                item.filename for item in archive.infolist()
                if not item.is_dir()
                and item.filename.lower().endswith((".csv", ".tsv", ".txt"))
                and item.file_size <= MAX_DOWNLOAD_BYTES
                and not item.filename.startswith(("/", "\\\\"))
                and ".." not in item.filename.replace("\\\\", "/").split("/")
            ]
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
                candidates = [
                    item.filename for item in archive.infolist()
                    if not item.is_dir()
                    and item.filename.lower().endswith((".csv", ".tsv", ".txt"))
                    and item.file_size <= MAX_DOWNLOAD_BYTES
                    and not item.filename.startswith(("/", "\\\\"))
                    and ".." not in item.filename.replace("\\\\", "/").split("/")
                ]
                chosen = member or (candidates[0] if len(candidates) == 1 else None)
                if chosen not in candidates:
                    raise OSDRError("Sélectionnez un fichier tabulaire présent dans l'archive.")
                info = archive.getinfo(chosen)
                if info.file_size > MAX_DOWNLOAD_BYTES:
                    raise OSDRError("Le tableau interne dépasse la limite d'aperçu.")
                return _tabular_frame(archive.read(chosen), chosen), f"{name} · {chosen}"
        except BadZipFile as exc:
            raise OSDRError("L'archive téléchargée n'est pas un ZIP valide.") from exc

    if not suffix.endswith((".csv", ".tsv", ".txt")):
        raise OSDRError("Format non pris en charge pour l'aperçu. Formats acceptés : CSV, TSV, TXT ou ZIP.")
    return _tabular_frame(payload, name), name
