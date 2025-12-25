from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple, Any
from urllib.parse import quote

import requests
from requests import RequestException, Response


class JFrogClient:
    """
    HTTP client minimale per Artifactory:
    - Bearer token (preferito) o API key
    - URL safe (percent-encoding dei segmenti)
    - Storage API per check di esistenza (robusta ai proxy)
    """

    def __init__(
        self,
        base_url: str,
        repo: str,
        access_token: Optional[str] = None,
        api_key: Optional[str] = None,
        connect_timeout: int = 10,
        read_timeout: int = 300,
        verbose: Optional[bool] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.repo = repo
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.verbose = bool(verbose or os.environ.get("JFROG_DEBUG"))
        self.session = requests.Session()
        if access_token:
            self.session.headers.update({"Authorization": f"Bearer {access_token}"})
        elif api_key:
            self.session.headers.update({"X-JFrog-Art-Api": api_key})

    # --- util ---------------------------------------------------------------

    def _log(self, event: str, **data) -> None:
        if self.verbose:
            import json

            print(json.dumps({"event": event, **data}), flush=True)

    def _compose_url(self, remote_path: str, matrix_props: str = "") -> str:
        """Percent-encode di repo e path, preservando '/' come separatore."""
        p = remote_path.lstrip("/")
        return (
            f"{self.base_url}/artifactory/"
            f"{quote(self.repo, safe='')}/"
            f"{quote(p, safe='/')}{matrix_props or ''}"
        )

    def _compose_storage_url(self, remote_path: str) -> str:
        """URL per Storage API (metadata)."""
        p = remote_path.lstrip("/")
        return (
            f"{self.base_url}/artifactory/api/storage/"
            f"{quote(self.repo, safe='')}/"
            f"{quote(p, safe='/')}"
        )

    # --- API: esistenza -----------------------------------------------------

    def stat(self, remote_path: str) -> Tuple[int, Optional[dict[str, Any]]]:
        """
        Interroga la Storage API per file/cartelle.
        Ritorna (status_code, json|None).
        """
        url = self._compose_storage_url(remote_path)
        try:
            r: Response = self.session.get(
                url, timeout=(self.connect_timeout, self.read_timeout)
            )
            self._log("http-storage", url=url, status=r.status_code)
            if r.headers.get("Content-Type", "").startswith("application/json"):
                try:
                    return r.status_code, r.json()
                except Exception:
                    return r.status_code, None
            return r.status_code, None
        except RequestException as e:
            self._log("http-storage-error", url=url, error=str(e))
            return 599, None  # pseudo-codice per errore di rete

    def exists(self, remote_path: str) -> Optional[bool]:
        """
        True  → esiste
        False → non esiste
        None  → indeterminato (errore rete o risposta anomala)
        """
        status, _ = self.stat(remote_path)
        if status == 200:
            return True
        if status == 404:
            return False
        return None

    # --- API: upload --------------------------------------------------------

    def put_file(
        self,
        local_path: Path,
        remote_path: str,
        sha1: Optional[str] = None,
        sha256: Optional[str] = None,
        matrix_props: Optional[str] = None,
        overwrite: bool = True,
    ) -> Tuple[int, str]:
        url = self._compose_url(remote_path, matrix_props or "")
        headers = {"Content-Type": "application/octet-stream"}
        if sha1:
            headers["X-Checksum-Sha1"] = sha1
        if sha256:
            headers["X-Checksum-Sha256"] = sha256
        # overwrite è gestito lato server; qui non forziamo nulla
        with Path(local_path).open("rb") as f:
            r = self.session.put(
                url,
                data=f,
                headers=headers,
                timeout=(self.connect_timeout, self.read_timeout),
            )
        self._log(
            "http-put",
            url=url,
            status=r.status_code,
            text=(r.text[:300] if hasattr(r, "text") else ""),
        )
        return r.status_code, url
