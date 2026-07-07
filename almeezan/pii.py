from __future__ import annotations

import re

from .models import Finding
from .text import compact_preview


PATTERNS: list[tuple[str, str, str, re.Pattern[str]]] = [
    ("EMAIL", "بريد إلكتروني", "medium", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("PHONE", "رقم هاتف", "medium", re.compile(r"(?<!\d)(?:\+?966|00966|0)?5\d{8}(?!\d)")),
    ("SAUDI_ID", "رقم هوية/إقامة سعودي", "high", re.compile(r"(?<![A-Za-z0-9_])[12]\d{9}(?![A-Za-z0-9_])")),
    ("API_KEY", "مفتاح API أو سر خدمة", "critical", re.compile(r"\b(?:sk|sk_live|sk_test|sk-ant|pplx|ghp|xoxb|cf|AKIA)[A-Za-z0-9_\-]{12,}\b")),
    ("JWT", "رمز JWT", "high", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("PRIVATE_KEY", "مفتاح خاص", "critical", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("IP_ADDRESS", "عنوان IP", "low", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("CREDENTIAL_URL", "رابط يحتوي اعتماد دخول", "high", re.compile(r"https?://[^/\s:@]+:[^@\s]+@[^/\s]+", re.I)),
]


def luhn_ok(value: str) -> bool:
    digits = [int(char) for char in re.sub(r"\D", "", value)]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def mask(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return value[:3] + "*" * max(4, len(value) - 7) + value[-4:]


def detect_pii(text: str, field: str = "output") -> list[Finding]:
    findings: list[Finding] = []
    for code, title, severity, pattern in PATTERNS:
        for match in pattern.finditer(text or ""):
            findings.append(
                Finding(
                    code=code,
                    title=title,
                    severity=severity,
                    detail=f"تم العثور على {title} في {field}.",
                    evidence=mask(match.group(0)),
                )
            )

    for match in re.finditer(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)", text or ""):
        value = match.group(0)
        if luhn_ok(value):
            findings.append(
                Finding(
                    code="PAYMENT_CARD",
                    title="رقم بطاقة دفع محتمل",
                    severity="critical",
                    detail=f"رقم بطاقة دفع صالح حسابياً ظهر في {field}.",
                    evidence=mask(value),
                )
            )

    return findings


def redact_text(text: str) -> str:
    value = text or ""
    for _code, _title, _severity, pattern in PATTERNS:
        value = pattern.sub(lambda m: mask(m.group(0)), value)
    value = re.sub(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)", lambda m: mask(m.group(0)) if luhn_ok(m.group(0)) else m.group(0), value)
    return compact_preview(value, 1200)
