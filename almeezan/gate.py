from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .core import evaluate_case
from .models import EvaluationCase, EvaluationResult
from .pii import PATTERNS, luhn_ok, redact_text
from .policy import INJECTION_PATTERNS, OPERATIONAL_RISK_PATTERNS
from .text import split_sentences


DROP_FINDING_CODES = {
    "UNSUPPORTED_CLAIM",
    "IGNORE_INSTRUCTIONS",
    "REVEAL_PROMPT",
    "JAILBREAK",
    "AR_IGNORE",
    "AR_REVEAL",
    "DESTRUCTIVE_COMMAND",
    "SHELL_PIPE",
    "DOCKER_SOCKET",
    "UNVERIFIED_GUARANTEE",
}


@dataclass
class GateResult:
    action: str
    original_verdict: str
    final_verdict: str
    safe_output: str
    changed: bool
    removed_sentences: list[str]
    evaluation: EvaluationResult
    rewritten_evaluation: EvaluationResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "original_verdict": self.original_verdict,
            "final_verdict": self.final_verdict,
            "safe_output": self.safe_output,
            "changed": self.changed,
            "removed_sentences": self.removed_sentences,
            "evaluation": self.evaluation.to_dict(),
            "rewritten_evaluation": self.rewritten_evaluation.to_dict() if self.rewritten_evaluation else None,
        }


def _problem_evidence(result: EvaluationResult) -> list[str]:
    evidence = []
    for signal in result.signals:
        for finding in signal.findings:
            if finding.code in DROP_FINDING_CODES and finding.evidence:
                evidence.append(finding.evidence.split(" | أقرب دليل:", 1)[0].strip())
    return evidence


def _sentence_matches(sentence: str, problem: str) -> bool:
    s = re.sub(r"\s+", " ", sentence).strip()
    p = re.sub(r"\s+", " ", problem).strip()
    if not s or not p:
        return False
    return s in p or p in s or (len(p) > 24 and p[:24] in s)


def _contains_blocking_secret(sentence: str) -> bool:
    for code, _title, severity, pattern in PATTERNS:
        if severity in {"high", "critical"} and pattern.search(sentence or ""):
            return True
    for match in re.finditer(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)", sentence or ""):
        if luhn_ok(match.group(0)):
            return True
    return False


def _contains_blocking_policy(sentence: str) -> bool:
    for code, _title, severity, pattern in [*INJECTION_PATTERNS, *OPERATIONAL_RISK_PATTERNS]:
        if severity in {"high", "critical"} and pattern.search(sentence or ""):
            return True
    return False


def propose_safe_output(case: EvaluationCase, result: EvaluationResult) -> tuple[str, list[str]]:
    problems = _problem_evidence(result)
    original_sentences = split_sentences(case.output)
    sentences = [(sentence, redact_text(sentence)) for sentence in original_sentences]
    if not sentences:
        return redact_text(case.output), []

    kept: list[str] = []
    removed: list[str] = []
    for original, redacted in sentences:
        should_drop = (
            _contains_blocking_secret(original)
            or _contains_blocking_policy(original)
            or any(_sentence_matches(original, problem) or _sentence_matches(redacted, problem) for problem in problems)
        )
        if should_drop:
            removed.append(redacted)
        else:
            kept.append(redacted)
    safe = " ".join(kept).strip()
    if not safe:
        safe = "[حُجب المخرج: لم تبق جمل مدعومة وآمنة بعد التنقيح.]"
    return safe, removed


def gate_case(case: EvaluationCase, ledger_path: str | None = "ledger/almeezan-ledger.jsonl", write_ledger: bool = True) -> GateResult:
    original = evaluate_case(case, ledger_path=ledger_path, write_ledger=write_ledger)
    if original.verdict == "PASS":
        return GateResult(
            action="allow",
            original_verdict=original.verdict,
            final_verdict=original.verdict,
            safe_output=case.output,
            changed=False,
            removed_sentences=[],
            evaluation=original,
        )

    safe_output, removed = propose_safe_output(case, original)
    rewritten_case = EvaluationCase(
        prompt=case.prompt,
        output=safe_output,
        evidence=list(case.evidence),
        model=case.model,
        use_case=case.use_case,
        risk_level=case.risk_level,
        metadata=dict(case.metadata),
    )
    rewritten = evaluate_case(rewritten_case, ledger_path=ledger_path, write_ledger=write_ledger)
    if rewritten.verdict == "PASS":
        action = "allow_after_rewrite"
    elif rewritten.verdict == "REVIEW":
        action = "review_after_rewrite"
    else:
        action = "block"
    return GateResult(
        action=action,
        original_verdict=original.verdict,
        final_verdict=rewritten.verdict,
        safe_output=safe_output,
        changed=safe_output != case.output,
        removed_sentences=removed,
        evaluation=original,
        rewritten_evaluation=rewritten,
    )
