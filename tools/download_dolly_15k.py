from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "external" / "databricks-dolly-15k"
RAW_PATH = OUT_DIR / "databricks-dolly-15k.jsonl"
CONVERTED_PATH = OUT_DIR / "databricks-dolly-15k.almeezan.jsonl"
SUMMARY_PATH = OUT_DIR / "SUMMARY.md"
SOURCE_PATH = OUT_DIR / "SOURCE.json"
URL = "https://huggingface.co/datasets/databricks/databricks-dolly-15k/resolve/main/databricks-dolly-15k.jsonl"


def download() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if RAW_PATH.exists() and RAW_PATH.stat().st_size > 1_000_000:
        print(f"raw exists: {RAW_PATH}")
        return

    print(f"downloading {URL}")
    with urllib.request.urlopen(URL, timeout=120) as response, RAW_PATH.open("wb") as handle:
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
            total += len(chunk)
            print(f"downloaded={total}", flush=True)


def load_records() -> list[dict[str, object]]:
    records = []
    with RAW_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def convert(records: list[dict[str, object]]) -> dict[str, int]:
    category_counts: dict[str, int] = {}
    with CONVERTED_PATH.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(records, start=1):
            category = str(row.get("category") or "unknown")
            context = str(row.get("context") or "").strip()
            category_counts[category] = category_counts.get(category, 0) + 1
            item = {
                "id": f"dolly-{index:05d}",
                "use_case": f"dolly:{category}",
                "model": "databricks-dolly-15k-reference-response",
                "risk_level": "medium",
                "prompt": row.get("instruction") or "",
                "output": row.get("response") or "",
                "evidence": (
                    [{"id": f"dolly-context-{index:05d}", "title": "Dolly context field", "text": context}]
                    if context
                    else []
                ),
                "metadata": {
                    "source_dataset": "databricks/databricks-dolly-15k",
                    "source_url": "https://huggingface.co/datasets/databricks/databricks-dolly-15k",
                    "category": category,
                    "has_context": bool(context),
                    "original_index": index,
                },
            }
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    return category_counts


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def write_metadata(records: list[dict[str, object]], category_counts: dict[str, int]) -> dict[str, object]:
    raw_sha = sha256(RAW_PATH)
    converted_sha = sha256(CONVERTED_PATH)
    source = {
        "dataset": "databricks/databricks-dolly-15k",
        "source_url": "https://huggingface.co/datasets/databricks/databricks-dolly-15k",
        "download_url": URL,
        "license": "CC BY-SA 3.0",
        "records": len(records),
        "raw_file": str(RAW_PATH),
        "converted_file": str(CONVERTED_PATH),
        "raw_sha256": raw_sha,
        "converted_sha256": converted_sha,
        "category_counts": dict(sorted(category_counts.items())),
        "prepared_at_epoch": int(time.time()),
    }
    SOURCE_PATH.write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Databricks Dolly 15k - Local Test Dataset",
        "",
        f"- Records: `{len(records)}`",
        "- Source: https://huggingface.co/datasets/databricks/databricks-dolly-15k",
        "- License: `CC BY-SA 3.0`",
        f"- Raw JSONL: `{RAW_PATH}`",
        f"- AlMeezan JSONL: `{CONVERTED_PATH}`",
        f"- Raw SHA256: `{raw_sha}`",
        "",
        "## Category Counts",
        "",
        "| Category | Records |",
        "| --- | ---: |",
    ]
    for category, count in sorted(category_counts.items()):
        lines.append(f"| {category} | {count} |")
    lines.append("")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")
    return source


def main() -> None:
    download()
    records = load_records()
    category_counts = convert(records)
    source = write_metadata(records, category_counts)
    print(json.dumps(source, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

