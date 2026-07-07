"""Central runtime configuration for Almeezan.

All deployment-specific values come from environment variables so the same
code runs unchanged on a laptop, a server, or inside a container:

- ``ALMEEZAN_HOME``: base directory for runtime state (default: project root).
- ``ALMEEZAN_LEDGER``: ledger JSONL path (default: ``<home>/ledger/almeezan-ledger.jsonl``).
- ``ALMEEZAN_SECRET``: HMAC secret file path (default: ``<home>/ledger/.almeezan-secret``).
- ``ALMEEZAN_API_KEY``: if set, every ``/api/*`` request must send ``X-API-Key``.
- ``ALMEEZAN_HOST`` / ``ALMEEZAN_PORT``: web service bind address (default ``127.0.0.1:8787``).
- ``ALMEEZAN_MAX_BODY_BYTES``: request body limit (default 1 MiB).
- ``ALMEEZAN_LOG_DIR``: structured log directory (default: ``<home>/logs``).
- ``ALMEEZAN_LOG_LEVEL``: ``DEBUG``/``INFO``/``WARNING``/``ERROR`` (default ``INFO``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name, "").strip()
    return Path(raw) if raw else default


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


@dataclass(frozen=True)
class AlmeezanConfig:
    home: Path = field(default_factory=lambda: PROJECT_ROOT)
    ledger_path: Path = field(default_factory=lambda: PROJECT_ROOT / "ledger" / "almeezan-ledger.jsonl")
    secret_path: Path = field(default_factory=lambda: PROJECT_ROOT / "ledger" / ".almeezan-secret")
    api_key: str = ""
    host: str = "127.0.0.1"
    port: int = 8787
    max_body_bytes: int = 1_048_576
    log_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "logs")
    log_level: str = "INFO"

    @property
    def auth_required(self) -> bool:
        return bool(self.api_key)


def load_config() -> AlmeezanConfig:
    home = _env_path("ALMEEZAN_HOME", PROJECT_ROOT)
    return AlmeezanConfig(
        home=home,
        ledger_path=_env_path("ALMEEZAN_LEDGER", home / "ledger" / "almeezan-ledger.jsonl"),
        secret_path=_env_path("ALMEEZAN_SECRET", home / "ledger" / ".almeezan-secret"),
        api_key=os.environ.get("ALMEEZAN_API_KEY", "").strip(),
        host=os.environ.get("ALMEEZAN_HOST", "127.0.0.1").strip() or "127.0.0.1",
        port=_env_int("ALMEEZAN_PORT", 8787),
        max_body_bytes=_env_int("ALMEEZAN_MAX_BODY_BYTES", 1_048_576, minimum=1024),
        log_dir=_env_path("ALMEEZAN_LOG_DIR", home / "logs"),
        log_level=os.environ.get("ALMEEZAN_LOG_LEVEL", "INFO").strip().upper() or "INFO",
    )
