from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_LEDGER = Path("ledger") / "almeezan-ledger.jsonl"
DEFAULT_SECRET = Path("ledger") / ".almeezan-secret"


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _secret(secret_path: Path) -> bytes:
    secret_path.parent.mkdir(parents=True, exist_ok=True)
    if not secret_path.exists():
        secret_path.write_text(secrets.token_hex(32), encoding="utf-8")
    return secret_path.read_text(encoding="utf-8").strip().encode("utf-8")


def _last_record_hash(path: Path) -> tuple[int, str]:
    if not path.exists():
        return 0, "GENESIS"
    last: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            last = json.loads(line)
    if not last:
        return 0, "GENESIS"
    return int(last.get("index", 0)), str(last.get("record_hash", "GENESIS"))


def append_record(payload: dict[str, Any], ledger_path: Path | str = DEFAULT_LEDGER, secret_path: Path | str = DEFAULT_SECRET) -> dict[str, Any]:
    path = Path(ledger_path)
    secret_file = Path(secret_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    last_index, previous_hash = _last_record_hash(path)
    payload_text = canonical_json(payload)
    payload_hash = sha256_text(payload_text)
    base = {
        "index": last_index + 1,
        "timestamp": datetime.now(UTC).isoformat(),
        "previous_hash": previous_hash,
        "payload_hash": payload_hash,
    }
    record_hash = sha256_text(canonical_json(base))
    seal = hmac.new(_secret(secret_file), record_hash.encode("utf-8"), hashlib.sha256).hexdigest()
    record = {**base, "record_hash": record_hash, "seal": seal, "payload": payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(record) + "\n")
    return {key: record[key] for key in ("index", "timestamp", "previous_hash", "payload_hash", "record_hash", "seal")}


def verify_ledger(ledger_path: Path | str = DEFAULT_LEDGER, secret_path: Path | str = DEFAULT_SECRET) -> dict[str, Any]:
    path = Path(ledger_path)
    secret_file = Path(secret_path)
    if not path.exists():
        return {"ok": True, "records": 0, "message": "ledger file does not exist yet"}

    secret = _secret(secret_file)
    previous = "GENESIS"
    count = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        expected_payload_hash = sha256_text(canonical_json(record.get("payload")))
        base = {
            "index": record.get("index"),
            "timestamp": record.get("timestamp"),
            "previous_hash": record.get("previous_hash"),
            "payload_hash": record.get("payload_hash"),
        }
        expected_record_hash = sha256_text(canonical_json(base))
        expected_seal = hmac.new(secret, expected_record_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        if record.get("previous_hash") != previous:
            return {"ok": False, "records": count, "line": line_number, "message": "broken hash chain"}
        if record.get("payload_hash") != expected_payload_hash:
            return {"ok": False, "records": count, "line": line_number, "message": "payload hash mismatch"}
        if record.get("record_hash") != expected_record_hash:
            return {"ok": False, "records": count, "line": line_number, "message": "record hash mismatch"}
        if record.get("seal") != expected_seal:
            return {"ok": False, "records": count, "line": line_number, "message": "seal mismatch"}
        previous = str(record["record_hash"])
        count += 1
    return {"ok": True, "records": count, "message": "ledger verified"}

