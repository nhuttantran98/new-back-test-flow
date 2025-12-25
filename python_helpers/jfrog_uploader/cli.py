from __future__ import annotations

import os
import json
import sys
from typing import Optional, Dict

import argparse
from dotenv import load_dotenv, find_dotenv

from jfrog_uploader.uploader import UploadError, upload_test_artifacts
from jfrog_uploader.models import JFrogConfig


def _parse_props(s: Optional[str]) -> Dict[str, str]:
    """
    Converte "--props 'k=v,k2=v2'" in dict.
    """
    if not s:
        return {}
    out: Dict[str, str] = {}
    for pair in s.split(","):
        pair = pair.strip()
        if not pair or "=" not in pair:
            raise ValueError(f"Invalid --props entry (expected k=v): {pair}")
        k, v = pair.split("=", 1)
        out[k.strip()] = os.path.expandvars(v.strip())
    return out


def main(argv: Optional[list[str]] = None) -> int:
    # Carica .env (cercandolo a partire dalla CWD verso l'alto)
    try:
        load_dotenv(find_dotenv(usecwd=True), override=False)
    except Exception:
        pass

    p = argparse.ArgumentParser(
        prog="jfroguploader",
        description="Upload artifact (dir/zip) + JSON results to JFrog Artifactory (API + CLI).",
    )
    p.add_argument(
        "--artifact_result",
        required=True,
        help="Artifact path: directory (auto-zipped) or .zip",
    )
    p.add_argument(
        "--json_result", required=True, help="Results JSON path: a .json file"
    )
    p.add_argument(
        "--dest", required=True, help="Destination segment (e.g. ./ws/WS_1.21.0)"
    )

    # JFrog connection
    p.add_argument(
        "--base-url",
        default=os.getenv("JFROG_URL"),
        help="JFrog base URL, e.g. https://<company>.jfrog.io",
    )
    p.add_argument(
        "--repo",
        default=os.getenv("JFROG_REPO", "generic-local"),
        help="Artifactory repository name",
    )
    p.add_argument(
        "--access-token",
        default=os.getenv("JFROG_ACCESS_TOKEN"),
        help="Access token (preferred)",
    )
    p.add_argument(
        "--api-key", default=os.getenv("JFROG_API_KEY"), help="API key (fallback)"
    )

    # Behaviour
    p.add_argument(
        "--props", default=os.getenv("PROPS"), help="Matrix properties, e.g. k=v,k2=v2"
    )
    p.add_argument(
        "--overwrite", action="store_true", help="Allow overwrite if remote file exists"
    )
    p.add_argument(
        "--dry-run", action="store_true", help="Print planned actions without uploading"
    )

    args = p.parse_args(argv)

    # Validazioni minime
    if not args.base_url:
        print("ERROR: Missing --base-url or JFROG_URL", file=sys.stderr)
        return 2

    jfrog: JFrogConfig = {
        "base_url": args.base_url,
        "access_token": args.access_token,
        "api_key": args.api_key,
    }

    try:
        summary = upload_test_artifacts(
            artifact_path=args.artifact_result,
            results_json_path=args.json_result,
            dest=args.dest,
            jfrog=jfrog,
            repo=args.repo,
            overwrite=args.overwrite,
            set_properties=_parse_props(args.props),
            dry_run=args.dry_run,
        )
        print(json.dumps(summary, indent=2))
        return 0
    except UploadError as e:
        # Mappa gli exit code su base HTTP status (se disponibile)
        status = getattr(e, "status", None)
        print(f"ERROR: {e}", file=sys.stderr)
        if status in (401, 403):
            return 30
        if status == 404:
            return 32
        if status is not None and 500 <= status <= 599:
            return 40
        return 31
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 50


if __name__ == "__main__":
    raise SystemExit(main())
