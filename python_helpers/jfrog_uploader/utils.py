from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

ARTIFACTORY_FIXED_PREFIX = "test/testreport/"


def normalize_dest(dest: str) -> str:
    """
    Normalizza un path "umano" in un path Artifactory-style.
    - rimuove leading "./" e backslash
    - usa '/' come separatore
    - collassa gli '//' duplicati
    """
    d = (dest or "").strip().lstrip("./\\").replace("\\", "/")
    while "//" in d:
        d = d.replace("//", "/")
    return d


def current_datetime(tz_name: str = "Europe/Rome") -> str:
    """
    Timestamp compatto per folder/suffisso: YYYYMMDDHHMMSS
    Fallback a UTC se la TZ non è disponibile (Windows senza tzdata).
    """
    tz = None
    if ZoneInfo is not None:
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            # opzionale: prova TZ env
            try:
                tz = ZoneInfo(os.environ.get("TZ", "UTC"))
            except Exception:
                tz = None
    import datetime as _dt

    dt = _dt.datetime.now(tz) if tz else _dt.datetime.utcnow()
    return dt.strftime("%Y%m%d%H%M%S")


def build_remote_folder_name(dest: str, ts: str, as_folder: bool = False) -> str:
    """
    Prepend fisso + dest normalizzato + timestamp (come subfolder o come suffisso).
    Restituisce SEMPRE una cartella che termina con '/'.
    Esempi:
      as_folder=False → test/testreport/ws/WS_1.21.0_20251014091503/
      as_folder=True  → test/testreport/ws/WS_1.21.0/20251014091503/
    """
    d = normalize_dest(dest).rstrip("/")
    base = (
        ARTIFACTORY_FIXED_PREFIX + d
        if not d.startswith(ARTIFACTORY_FIXED_PREFIX)
        else d
    )
    if ts:
        base = f"{base}/{ts}" if as_folder else f"{base}_{ts}"
    if not base.endswith("/"):
        base += "/"
    return base


def ensure_zip(path: Path) -> Path:
    """
    Se 'path' è una directory, crea uno zip temporaneo; se è file, lo restituisce.
    """
    path = Path(path)
    if path.is_file():
        return path
    if not path.exists():
        raise FileNotFoundError(f"Artifact path not found: {path}")
    # zip tmp
    tmpdir = Path(tempfile.mkdtemp(prefix="artifact_zip_"))
    zip_path = tmpdir / f"{path.name}.zip"
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", root_dir=str(path))
    return zip_path


def _hash_of_file(p: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with Path(p).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha1_of_file(p: Path) -> str:
    return _hash_of_file(p, "sha1")


def sha256_of_file(p: Path) -> str:
    return _hash_of_file(p, "sha256")


def as_matrix_properties(props: dict[str, str] | None) -> str:
    """
    Converte un dict in matrix params: ;k=v;k2=v2
    (Non fa URL-encoding; ci pensa la costruzione URL lato client)
    """
    if not props:
        return ""
    parts = []
    for k, v in props.items():
        if v is None:
            continue
        parts.append(f";{k}={v}")
    return "".join(parts)
