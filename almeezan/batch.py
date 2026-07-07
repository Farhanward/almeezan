from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .core import evaluate_case
from .evidence import augment_case_with_index
from .models import EvaluationCase
from .reports import result_to_markdown


def load_case(path: Path) -> EvaluationCase:
    data = json.loads(path.read_text(encoding="utf-8"))
    return EvaluationCase.from_dict(data, base_dir=str(path.parent))


def run_batch(
    input_dir: Path,
    out_dir: Path,
    evidence_index: Path | None = None,
    top_k: int = 5,
    write_ledger: bool = True,
    ledger_path: Path | str = "ledger/almeezan-ledger.jsonl",
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = sorted(input_dir.glob("*.json"))
    results = []
    for case_path in cases:
        case = load_case(case_path)
        augment_case_with_index(case, evidence_index, top_k=top_k)
        result = evaluate_case(case, ledger_path=ledger_path, write_ledger=write_ledger)
        report_path = out_dir / f"{case_path.stem}.md"
        json_path = out_dir / f"{case_path.stem}.json"
        report_path.write_text(result_to_markdown(result), encoding="utf-8")
        json_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        results.append({"case": case_path.name, "report": str(report_path), "json": str(json_path), "result": result})

    verdicts = Counter(item["result"].verdict for item in results)
    avg_score = sum(item["result"].score for item in results) / len(results) if results else 0.0
    summary = {
        "case_count": len(results),
        "average_score": round(avg_score, 2),
        "verdicts": dict(verdicts),
        "items": [
            {
                "case": item["case"],
                "score": round(item["result"].score, 2),
                "verdict": item["result"].verdict,
                "report": item["report"],
            }
            for item in results
        ],
    }
    write_summary(out_dir / "batch_summary.md", summary)
    (out_dir / "batch_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def write_summary(path: Path, summary: dict[str, object]) -> None:
    verdicts = summary.get("verdicts", {})
    lines = [
        "# ملخص تشغيل الميزان",
        "",
        f"- عدد الحالات: `{summary.get('case_count', 0)}`",
        f"- متوسط الدرجة: `{summary.get('average_score', 0)}`",
        f"- PASS: `{dict(verdicts).get('PASS', 0)}`",
        f"- REVIEW: `{dict(verdicts).get('REVIEW', 0)}`",
        f"- BLOCK: `{dict(verdicts).get('BLOCK', 0)}`",
        "",
        "## الحالات",
        "",
        "| الحالة | الدرجة | الحكم | التقرير |",
        "| --- | ---: | --- | --- |",
    ]
    for item in summary.get("items", []):
        report = str(item["report"])
        lines.append(f"| {item['case']} | {item['score']} | {item['verdict']} | `{report}` |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")

