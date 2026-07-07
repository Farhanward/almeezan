from __future__ import annotations

import re
import unicodedata


ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
TOKEN_RE = re.compile(r"[\u0600-\u06FFa-zA-Z0-9_]+")

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
    "و",
    "في",
    "من",
    "على",
    "عن",
    "إلى",
    "الى",
    "هو",
    "هي",
    "هذا",
    "هذه",
    "ذلك",
    "تلك",
    "كما",
    "أن",
    "ان",
    "إن",
    "كان",
    "كانت",
    "كل",
    "لا",
    "ما",
    "أو",
    "او",
    "ثم",
    "لكن",
    "لدى",
    "عبر",
    "بين",
    "بعد",
    "قبل",
    "أي",
    "اي",
}


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKC", text or "")
    value = ARABIC_DIACRITICS.sub("", value)
    value = value.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    value = value.replace("ى", "ي").replace("ة", "ه")
    return value.lower()


def tokenize(text: str) -> list[str]:
    tokens = TOKEN_RE.findall(normalize(text))
    return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]


def unique_tokens(text: str) -> set[str]:
    return set(tokenize(text))


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text or "").strip()
    if not normalized:
        return []
    parts = re.split(r"(?<=[.!?؟؛])\s+|[\n\r]+|(?:\s+-\s+)", normalized)
    sentences = []
    for part in parts:
        item = part.strip(" \t-•*")
        if len(tokenize(item)) >= 3:
            sentences.append(item)
    return sentences


def compact_preview(text: str, limit: int = 140) -> str:
    value = re.sub(r"\s+", " ", text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."

