from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass
from typing import Optional
from .models import UploadSummary

from .models import UploadSummary, JFrogConfig
from .utils import (
    ensure_zip,
    sha1_of_file,
    sha256_of_file,
    build_remote_folder_name,
    current_datetime,
    normalize_dest,
    as_matrix_properties,
)
from .client import JFrogClient


class UploadError(RuntimeError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def upload_test_artifacts(
    artifact_path: str,
    results_json_path: str,
    dest: str,
    jfrog: JFrogConfig,
    repo: str,
    overwrite: bool = False,
    set_properties: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> UploadSummary:
    """
    Flusso:
      1) normalizza input e zippa se necessario
      2) calcola checksum
      3) costruisce il percorso remoto con dest + timestamp (suffisso)
      4) (dry-run) stampa URLs + checksum
      5) (reale) verifica esistenza via Storage API (no HEAD fragile)
      6) PUT artifact e JSON
      7) ritorna il riepilogo
    """
    # --- input ---
    artifact_in = Path(artifact_path)
    results_in = Path(results_json_path)
    if not artifact_in.exists():
        raise FileNotFoundError(f"Artifact path not found: {artifact_in}")
    if not results_in.exists() or results_in.suffix.lower() != ".json":
        raise FileNotFoundError(f"Results JSON file not found or invalid: {results_in}")

    zip_or_file = ensure_zip(artifact_in)  # dir→zip, file→file

    # --- checksum ---
    a_sha1 = sha1_of_file(zip_or_file)
    a_sha256 = sha256_of_file(zip_or_file)
    r_sha1 = sha1_of_file(results_in)
    r_sha256 = sha256_of_file(results_in)

    # --- percorso remoto ---
    ts = current_datetime()  # YYYYMMDDHHMMSS

    remote_folder = build_remote_folder_name(
        dest, ts, as_folder=False
    )  # es. .../WS_1.21.0_<ts>/

    remote_folder = normalize_dest(remote_folder)

    if not remote_folder.endswith("/"):
        remote_folder += "/"

    artifact_remote_path = f"{remote_folder}{zip_or_file.name}"
    results_remote_path = f"{remote_folder}{results_in.name}"

    # --- client ---
    base_url = (jfrog.get("base_url") or "").rstrip("/")
    if not base_url:
        raise ValueError("jfrog.base_url is required")

    client = JFrogClient(
        base_url=base_url,
        repo=repo,
        access_token=jfrog.get("access_token"),
        api_key=jfrog.get("api_key"),
    )

    # --- props ---
    matrix_props = as_matrix_properties(set_properties)

    # --- dry-run ---
    artifact_url = (
        f"{base_url}/artifactory/{repo}/{remote_folder}{zip_or_file.name}{matrix_props}"
    )
    results_url = (
        f"{base_url}/artifactory/{repo}/{remote_folder}{results_in.name}{matrix_props}"
    )
    summary: UploadSummary = {
        "artifact_url": artifact_url,
        "results_url": results_url,
        "checksums": {
            "artifact": {"sha256": a_sha256, "sha1": a_sha1},
            "results": {"sha256": r_sha256, "sha1": r_sha1},
        },
    }
    if dry_run:
        return summary

    # --- check di esistenza ROBUSTO (senza HEAD) ---
    if not overwrite:
        # Se il file esiste → blocca. Se non esiste → ok. Se indeterminato → fall-back.
        exists_art = client.exists(artifact_remote_path)
        if exists_art is True:
            raise UploadError(
                f"Remote artifact exists: {artifact_remote_path}. Use --overwrite to replace.",
                status=409,
            )
        exists_res = client.exists(results_remote_path)
        if exists_res is True:
            raise UploadError(
                f"Remote results JSON exists: {results_remote_path}. Use --overwrite to replace.",
                status=409,
            )
        # Se uno dei due è indeterminato (None), tentiamo un fall-back: list del folder
        if exists_art is None or exists_res is None:
            stat_folder = client.stat(remote_folder)[0]
            # Se la cartella esiste ma non riusciamo a determinare i file, lasciamo decidere al PUT
            # (Artifactory restituirà 201 se nuovo, 200 se overwrite; noi NON intendiamo overwritare)
            # quindi un 200 alla PUT lo tratteremo come errore di policy quando overwrite=False.
            pass

    # --- upload artifact ---
    code_art, url_art = client.put_file(
        local_path=zip_or_file,
        remote_path=artifact_remote_path,
        sha1=a_sha1,
        sha256=a_sha256,
        matrix_props=matrix_props,
        overwrite=True,  # il server gestisce l'overwrite; la policy è sopra
    )
    # Policy: se overwrite=False e il server risponde 200 (sovrascrittura), consideralo errore.
    if code_art >= 300 or (code_art == 200 and not overwrite):
        raise UploadError(
            f"Artifact upload failed ({code_art}) → {url_art}", status=code_art
        )

    # --- upload results json ---
    code_res, url_res = client.put_file(
        local_path=results_in,
        remote_path=results_remote_path,
        sha1=r_sha1,
        sha256=r_sha256,
        matrix_props=matrix_props,
        overwrite=True,
    )
    if code_res >= 300 or (code_res == 200 and not overwrite):
        raise UploadError(
            f"Results JSON upload failed ({code_res}) → {url_res}", status=code_res
        )

    return summary


# --- Wrapper "safe" per integrazioni che non vogliono eccezioni ----------------


@dataclass(frozen=True)
class UploadResult:
    ok: bool
    exit_code: int
    http_status: Optional[int]
    summary: Optional[UploadSummary]
    error: Optional[str]


def upload_test_artifacts_safe(
    *,
    artifact_path: str,
    results_json_path: str,
    dest: str,
    jfrog: JFrogConfig,
    repo: str = "generic-local",
    overwrite: bool = False,
    set_properties: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
) -> UploadResult:
    """
    Safe wrapper: non lancia eccezioni; ritorna un UploadResult con exit_code.
    La firma è esplicita per chiarezza e autocompletion nell'orchestratore.
    """
    try:
        summary = upload_test_artifacts(
            artifact_path=artifact_path,
            results_json_path=results_json_path,
            dest=dest,
            jfrog=jfrog,
            repo=repo,
            overwrite=overwrite,
            set_properties=set_properties,
            dry_run=dry_run,
        )
        return UploadResult(
            ok=True, exit_code=0, http_status=0, summary=summary, error=None
        )
    except UploadError as e:
        http = getattr(e, "status", None)
        if http in (401, 403):
            code = 30
        elif http == 404:
            code = 32
        elif http is not None and 500 <= http <= 599:
            code = 40
        else:
            code = 31
        return UploadResult(
            ok=False, exit_code=code, http_status=http, summary=None, error=str(e)
        )
    except (FileNotFoundError, ValueError) as e:
        return UploadResult(
            ok=False, exit_code=2, http_status=None, summary=None, error=str(e)
        )
    except Exception as e:
        return UploadResult(
            ok=False, exit_code=50, http_status=None, summary=None, error=str(e)
        )
