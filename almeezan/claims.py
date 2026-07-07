from __future__ import annotations

import re

from .models import Evidence, Finding, Signal
from .text import compact_preview, normalize, split_sentences, unique_tokens


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\b\d+(?:[.,]\d+)?%?\b", text or ""))


def _contradiction_cap(claim: str, evidence_text: str) -> float | None:
    claim_n = normalize(claim)
    evidence_n = normalize(evidence_text)
    negates_evidence = any(marker in evidence_n for marker in ("لا يوجد", "لا توجد", "ليس هناك", "غير مثبت", "no evidence", "does not", "not guarantee"))
    if not negates_evidence:
        return None

    guarantee_claim = any(marker in claim_n for marker in ("تضمن", "ضمان", "ارباح", "دخل", "guarantee", "profit", "income"))
    superiority_claim = any(marker in claim_n for marker in ("افضل", "الاولي", "اول", "رقم 1", "number one", "best", "leading"))
    if guarantee_claim and any(marker in evidence_n for marker in ("ضمان", "ارباح", "دخل", "guarantee", "profit", "income")):
        return 0.18
    if superiority_claim and any(marker in evidence_n for marker in ("الاولي", "افضل", "best", "number one", "leading")):
        return 0.18
    return None


def _best_evidence_score(claim: str, evidence: list[Evidence]) -> tuple[float, Evidence | None]:
    claim_tokens = unique_tokens(claim)
    if not claim_tokens:
        return 0.0, None

    claim_numbers = _numbers(claim)
    best_score = 0.0
    best_item: Evidence | None = None

    for item in evidence:
        evidence_tokens = unique_tokens(item.text)
        if not evidence_tokens:
            continue
        overlap = claim_tokens & evidence_tokens
        token_score = len(overlap) / max(1, len(claim_tokens))
        if claim_numbers:
            evidence_numbers = _numbers(item.text)
            if not claim_numbers <= evidence_numbers:
                token_score *= 0.45
        exact_phrase_bonus = 0.15 if compact_preview(claim, 70).lower() in item.text.lower() else 0.0
        score = min(1.0, token_score + exact_phrase_bonus)
        cap = _contradiction_cap(claim, item.text)
        if cap is not None:
            score = min(score, cap)
        if score > best_score:
            best_score = score
            best_item = item

    return best_score, best_item


def _short_answer_signal(output: str, evidence: list[Evidence], prompt: str = "") -> Signal:
    output_tokens = unique_tokens(output)
    if not output_tokens:
        return Signal(
            name="اتساق الأدلة",
            score=100.0,
            status="pass",
            summary="لا توجد ادعاءات كافية للفحص.",
        )

    prompt_tokens = unique_tokens(prompt)
    evidence_tokens = unique_tokens("\n".join(item.text for item in evidence))
    has_evidence = bool(evidence_tokens)
    if has_evidence and output_tokens & evidence_tokens:
        return Signal(
            name="اتساق الأدلة",
            score=100.0,
            status="pass",
            summary="إجابة قصيرة مدعومة بظهورها في الأدلة.",
        )
    if not has_evidence and output_tokens <= prompt_tokens:
        return Signal(
            name="اتساق الأدلة",
            score=100.0,
            status="pass",
            summary="إجابة قصيرة مستخرجة من خيارات السؤال نفسه.",
        )

    code = "NO_EVIDENCE_SHORT_ANSWER" if not has_evidence else "UNSUPPORTED_SHORT_ANSWER"
    detail = "إجابة قصيرة لا يمكن إثباتها دون دليل." if not has_evidence else "إجابة قصيرة لا تظهر في الأدلة المقدمة."
    return Signal(
        name="اتساق الأدلة",
        score=0.0,
        status="review" if not evidence else "block",
        summary="إجابة قصيرة غير مثبتة.",
        findings=[
            Finding(
                code=code,
                title="إجابة قصيرة غير مثبتة",
                severity="medium" if not evidence else "high",
                detail=detail,
                evidence=compact_preview(output),
            )
        ],
    )


def evaluate_faithfulness(output: str, evidence: list[Evidence], prompt: str = "") -> Signal:
    claims = split_sentences(output)
    if not claims:
        return _short_answer_signal(output, evidence, prompt)
    if not evidence:
        return Signal(
            name="اتساق الأدلة",
            score=0.0,
            status="review",
            summary="لا توجد أدلة مرجعية، لذلك لا يمكن إثبات الادعاءات.",
            findings=[
                Finding(
                    code="NO_EVIDENCE",
                    title="غياب الأدلة",
                    severity="high",
                    detail="أدخل أدلة أو ملفات evidence_paths حتى يستطيع الميزان وزن المصداقية.",
                )
            ],
        )

    supported = 0
    weak: list[Finding] = []
    for claim in claims:
        score, item = _best_evidence_score(claim, evidence)
        if score >= 0.48:
            supported += 1
        else:
            weak.append(
                Finding(
                    code="UNSUPPORTED_CLAIM",
                    title="ادعاء غير مثبت",
                    severity="high" if score < 0.25 else "medium",
                    detail=f"لم يجد الميزان دعماً كافياً لهذا الادعاء. أفضل تطابق: {score:.0%}.",
                    evidence=f"{compact_preview(claim)}" + (f" | أقرب دليل: {item.title}" if item else ""),
                )
            )

    score = 100.0 * supported / len(claims)
    status = "pass" if score >= 75 else "review" if score >= 45 else "block"
    summary = f"{supported}/{len(claims)} ادعاء مدعوم بالأدلة."
    return Signal(name="اتساق الأدلة", score=score, status=status, summary=summary, findings=weak[:12])
