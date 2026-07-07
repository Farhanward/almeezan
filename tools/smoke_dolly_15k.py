from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almeezan.core import evaluate_case
from almeezan.models import EvaluationCase

DATA = ROOT / "data" / "external" / "databricks-dolly-15k" / "databricks-dolly-15k.almeezan.jsonl"
OUT_JSON = ROOT / "reports" / "dolly_15k_smoke_summary.json"
OUT_MD = ROOT / "reports" / "dolly_15k_smoke_summary.md"


def main() -> None:
    verdicts: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    scores = []
    with_context = 0
    total = 0

    with DATA.open("r", encoding="utf-8") as handle:
        for total, line in enumerate(handle, start=1):
            row = json.loads(line)
            case = EvaluationCase.from_dict(row)
            result = evaluate_case(case, write_ledger=False)
            verdicts[result.verdict] += 1
            category = str(row.get("metadata", {}).get("category", "unknown"))
            categories[category] += 1
            scores.append(result.score)
            if row.get("evidence"):
                with_context += 1
            if total % 1000 == 0:
                print(f"evaluated={total}", flush=True)

    summary = {
        "dataset": "databricks/databricks-dolly-15k",
        "records": total,
        "with_context_evidence": with_context,
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "verdicts": dict(verdicts),
        "categories": dict(categories),
        "input": str(DATA),
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Dolly 15k Smoke Test",
        "",
        f"- Records evaluated: `{total}`",
        f"- Records with context evidence: `{with_context}`",
        f"- Average score: `{summary['average_score']}`",
        "",
        "## Verdicts",
        "",
        "| Verdict | Count |",
        "| --- | ---: |",
    ]
    for verdict, count in sorted(verdicts.items()):
        lines.append(f"| {verdict} | {count} |")
    lines.extend(["", "## Categories", "", "| Category | Count |", "| --- | ---: |"])
    for category, count in sorted(categories.items()):
        lines.append(f"| {category} | {count} |")
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
