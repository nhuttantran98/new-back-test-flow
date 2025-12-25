from typing import TypedDict, Optional, Dict


class JFrogConfig(TypedDict, total=False):
    """Data contract of JFrog connection settings. This is used by the uploader: receives a JFrogConfig and builds a JFrogClient"""

    base_url: str  # e.g. https://<datalogic>.jfrog.io
    access_token: Optional[str]
    api_key: Optional[str]
    project: Optional[
        str
    ]  # not required for basic uploads. might be useful in the future for project-scoped uploads


class UploadSummary(TypedDict, total=False):
    """Structured output received from the API and printed by the CLI.
    This is constructed and used by the uploader function and the CLI to print a summary
    """

    artifact_url: str
    results_url: str
    checksums: Dict[
        str, Dict[str, str]
    ]  # {"artifact": {"sha256": "...", "sha1": "..."}, "results": {...}}
