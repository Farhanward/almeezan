from __future__ import annotations

from typing import Any

from .models import EvaluationResult, Finding


def _verdict_ar(verdict: str) -> str:
    return {"PASS": "مقبول", "REVIEW": "مراجعة", "BLOCK": "حجب"}.get(verdict, verdict)


def _finding_line(finding: Finding) -> str:
    evidence = f" — `{finding.evidence}`" if finding.evidence else ""
    return f"- **{finding.severity} / {finding.title}:** {finding.detail}{evidence}"


def result_to_markdown(result: EvaluationResult) -> str:
    lines: list[str] = []
    lines.append("# تقرير الميزان")
    lines.append("")
    lines.append(f"- رقم الحكم: `{result.id}`")
    lines.append(f"- الوقت: `{result.created_at}`")
    lines.append(f"- الحالة: **{_verdict_ar(result.verdict)}** (`{result.verdict}`)")
    lines.append(f"- الدرجة: **{result.score:.1f}/100**")
    lines.append(f"- القرار: {result.decision}")
    lines.append("")
    lines.append("## الإشارات")
    lines.append("")
    lines.append("| الإشارة | الدرجة | الحالة | الملخص |")
    lines.append("| --- | ---: | --- | --- |")
    for signal in result.signals:
        lines.append(f"| {signal.name} | {signal.score:.1f} | {signal.status} | {signal.summary} |")
    lines.append("")
    lines.append("## الملاحظات")
    lines.append("")
    any_findings = False
    for signal in result.signals:
        if not signal.findings:
            continue
        any_findings = True
        lines.append(f"### {signal.name}")
        lines.extend(_finding_line(finding) for finding in signal.findings)
        lines.append("")
    if not any_findings:
        lines.append("لا توجد ملاحظات مانعة.")
        lines.append("")
    if result.ledger:
        lines.append("## سجل التدقيق")
        lines.append("")
        lines.append(f"- رقم السجل: `{result.ledger.get('index')}`")
        lines.append(f"- Hash الحكم: `{result.ledger.get('record_hash')}`")
        lines.append(f"- Hash السابق: `{result.ledger.get('previous_hash')}`")
        lines.append("")
    return "\n".join(lines)


def gate_to_markdown(gate: Any) -> str:
    lines = [
        "# تقرير بوابة الميزان",
        "",
        f"- الإجراء: `{gate.action}`",
        f"- الحكم الأصلي: `{gate.original_verdict}`",
        f"- الحكم النهائي: `{gate.final_verdict}`",
        f"- تم تعديل المخرج: `{gate.changed}`",
        "",
        "## المخرج الآمن",
        "",
        gate.safe_output,
        "",
    ]
    if gate.removed_sentences:
        lines.append("## الجمل المحذوفة")
        lines.append("")
        for sentence in gate.removed_sentences:
            lines.append(f"- {sentence}")
        lines.append("")
    lines.append("## الحكم الأصلي")
    lines.append("")
    lines.append(result_to_markdown(gate.evaluation))
    if gate.rewritten_evaluation:
        lines.append("")
        lines.append("## الحكم بعد التنقيح")
        lines.append("")
        lines.append(result_to_markdown(gate.rewritten_evaluation))
    return "\n".join(lines)
