from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from almeezan.core import evaluate_case
from almeezan.models import EvaluationCase
from almeezan.text import compact_preview


DATA = ROOT / "data" / "external" / "databricks-dolly-15k" / "databricks-dolly-15k.almeezan.jsonl"
OUT_JSON = ROOT / "reports" / "dolly_15k_review.json"
OUT_MD = ROOT / "reports" / "dolly_15k_review.md"


def finding_codes(result: Any) -> list[str]:
    codes = []
    for signal in result.signals:
        for finding in signal.findings:
            codes.append(finding.code)
    return codes


def sample_record(row: dict[str, Any], result: Any) -> dict[str, Any]:
    evidence_signal = next(signal for signal in result.signals if signal.name == "اتساق الأدلة")
    privacy_signal = next(signal for signal in result.signals if signal.name == "الخصوصية والأسرار")
    policy_signal = next(signal for signal in result.signals if signal.name == "السياسة والمخاطر")
    return {
        "id": row["id"],
        "category": row.get("metadata", {}).get("category"),
        "has_context": bool(row.get("evidence")),
        "score": round(result.score, 2),
        "verdict": result.verdict,
        "evidence_score": round(evidence_signal.score, 2),
        "privacy_score": round(privacy_signal.score, 2),
        "policy_score": round(policy_signal.score, 2),
        "finding_codes": finding_codes(result),
        "prompt_preview": compact_preview(str(row.get("prompt", "")), 220),
        "output_preview": compact_preview(str(row.get("output", "")), 260),
        "evidence_preview": compact_preview(str(row.get("evidence", [{}])[0].get("text", "")) if row.get("evidence") else "", 260),
    }


def main() -> None:
    totals: Counter[str] = Counter()
    by_context: dict[str, Counter[str]] = {"with_context": Counter(), "without_context": Counter()}
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    finding_counter: Counter[str] = Counter()
    signal_statuses: dict[str, Counter[str]] = defaultdict(Counter)
    samples: dict[str, list[dict[str, Any]]] = {"PASS": [], "REVIEW": [], "BLOCK": []}
    edge_samples: dict[str, list[dict[str, Any]]] = {
        "pass_without_context": [],
        "block_with_context": [],
        "review_with_context": [],
        "review_without_context": [],
    }

    total = 0
    with DATA.open("r", encoding="utf-8") as handle:
        for total, line in enumerate(handle, start=1):
            row = json.loads(line)
            case = EvaluationCase.from_dict(row)
            result = evaluate_case(case, write_ledger=False)
            verdict = result.verdict
            category = str(row.get("metadata", {}).get("category", "unknown"))
            has_context = bool(row.get("evidence"))
            totals[verdict] += 1
            by_context["with_context" if has_context else "without_context"][verdict] += 1
            by_category[category][verdict] += 1
            finding_counter.update(finding_codes(result))
            for signal in result.signals:
                signal_statuses[signal.name][signal.status] += 1

            if len(samples[verdict]) < 8:
                samples[verdict].append(sample_record(row, result))
            if verdict == "PASS" and not has_context and len(edge_samples["pass_without_context"]) < 8:
                edge_samples["pass_without_context"].append(sample_record(row, result))
            if verdict == "BLOCK" and has_context and len(edge_samples["block_with_context"]) < 8:
                edge_samples["block_with_context"].append(sample_record(row, result))
            if verdict == "REVIEW" and has_context and len(edge_samples["review_with_context"]) < 8:
                edge_samples["review_with_context"].append(sample_record(row, result))
            if verdict == "REVIEW" and not has_context and len(edge_samples["review_without_context"]) < 8:
                edge_samples["review_without_context"].append(sample_record(row, result))

            if total % 2000 == 0:
                print(f"reviewed={total}", flush=True)

    summary = {
        "records": total,
        "verdicts": dict(totals),
        "by_context": {key: dict(value) for key, value in by_context.items()},
        "by_category": {key: dict(value) for key, value in sorted(by_category.items())},
        "top_finding_codes": finding_counter.most_common(30),
        "signal_statuses": {key: dict(value) for key, value in signal_statuses.items()},
        "samples": samples,
        "edge_samples": edge_samples,
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(summary)
    print(json.dumps({k: summary[k] for k in ("records", "verdicts", "by_context", "top_finding_codes")}, ensure_ascii=False, indent=2))


def write_markdown(summary: dict[str, Any]) -> None:
    lines = [
        "# مراجعة مخرجات Dolly 15k",
        "",
        f"- السجلات: `{summary['records']}`",
        "",
        "## الأحكام",
        "",
        "| الحكم | العدد |",
        "| --- | ---: |",
    ]
    for verdict, count in sorted(summary["verdicts"].items()):
        lines.append(f"| {verdict} | {count} |")

    lines.extend(["", "## حسب وجود دليل context", "", "| المجموعة | PASS | REVIEW | BLOCK |", "| --- | ---: | ---: | ---: |"])
    for name, counts in summary["by_context"].items():
        lines.append(f"| {name} | {counts.get('PASS', 0)} | {counts.get('REVIEW', 0)} | {counts.get('BLOCK', 0)} |")

    lines.extend(["", "## أكثر أسباب الملاحظات", "", "| الكود | العدد |", "| --- | ---: |"])
    for code, count in summary["top_finding_codes"][:15]:
        lines.append(f"| {code} | {count} |")

    lines.extend(["", "## حالات حافة مختصرة", ""])
    for group, records in summary["edge_samples"].items():
        lines.append(f"### {group}")
        for item in records[:5]:
            lines.append(
                f"- `{item['id']}` {item['category']} score={item['score']} verdict={item['verdict']} "
                f"evidence={item['evidence_score']} findings={','.join(item['finding_codes']) or '-'}"
            )
            lines.append(f"  - prompt: {item['prompt_preview']}")
            lines.append(f"  - output: {item['output_preview']}")
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

