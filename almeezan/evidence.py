from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import Evidence
from .text import compact_preview, split_sentences, tokenize, unique_tokens


DEFAULT_EXTENSIONS = {".md", ".txt", ".json", ".jsonl", ".yml", ".yaml", ".html", ".htm", ".csv"}


@dataclass
class EvidenceChunk:
    id: str
    title: str
    text: str
    source_path: str
    tokens: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "source_path": self.source_path,
            "tokens": self.tokens,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceChunk":
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            text=str(data["text"]),
            source_path=str(data["source_path"]),
            tokens=[str(token) for token in data.get("tokens", [])],
        )

    def to_evidence(self) -> Evidence:
        return Evidence(id=self.id, title=self.title, text=self.text)


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1256", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def _normalize_json_text(text: str) -> str:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text
    return json.dumps(data, ensure_ascii=False, indent=2)


def _looks_like_case_file(path: Path, text: str) -> bool:
    if path.suffix.lower() != ".json":
        return False
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(data, dict) and "prompt" in data and "output" in data


def _chunk_text(text: str, max_chars: int = 1800) -> list[str]:
    normalized = re.sub(r"\r\n?", "\n", text or "").strip()
    if not normalized:
        return []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", normalized) if part.strip()]
    if len(paragraphs) <= 1:
        paragraphs = split_sentences(normalized) or [normalized]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            for index in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[index : index + max_chars].strip())
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) > max_chars and current:
            chunks.append(current.strip())
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current.strip())
    return chunks


def build_index(source: Path, out_path: Path, extensions: set[str] | None = None) -> dict[str, Any]:
    allowed = extensions or DEFAULT_EXTENSIONS
    source = source.resolve()
    files = []
    if source.is_file():
        files = [source]
    else:
        files = [
            item
            for item in source.rglob("*")
            if item.is_file() and item.suffix.lower() in allowed and not any(part.startswith(".") for part in item.parts)
        ]

    chunks: list[EvidenceChunk] = []
    for file_path in sorted(files):
        text = read_text(file_path)
        if _looks_like_case_file(file_path, text):
            continue
        if file_path.suffix.lower() in {".json", ".jsonl"}:
            text = _normalize_json_text(text)
        for index, chunk_text in enumerate(_chunk_text(text), start=1):
            digest = hashlib.sha256(f"{file_path}:{index}:{chunk_text}".encode("utf-8")).hexdigest()[:16]
            title = f"{file_path.name}#{index}"
            chunks.append(
                EvidenceChunk(
                    id=f"chunk-{digest}",
                    title=title,
                    text=chunk_text,
                    source_path=str(file_path),
                    tokens=sorted(unique_tokens(chunk_text)),
                )
            )

    payload = {
        "version": 1,
        "source": str(source),
        "file_count": len(files),
        "chunk_count": len(chunks),
        "chunks": [chunk.to_dict() for chunk in chunks],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def load_index(path: Path) -> list[EvidenceChunk]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [EvidenceChunk.from_dict(item) for item in data.get("chunks", [])]


def retrieve(index_path: Path, query: str, top_k: int = 5) -> list[Evidence]:
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return []
    ranked: list[tuple[float, EvidenceChunk]] = []
    for chunk in load_index(index_path):
        chunk_tokens = set(chunk.tokens)
        if not chunk_tokens:
            continue
        overlap = query_tokens & chunk_tokens
        coverage = len(overlap) / max(1, len(query_tokens))
        density = len(overlap) / max(1, len(chunk_tokens))
        score = (coverage * 0.76) + (density * 0.24)
        if score > 0:
            ranked.append((score, chunk))
    ranked.sort(key=lambda item: item[0], reverse=True)
    evidence = []
    for score, chunk in ranked[:top_k]:
        evidence.append(
            Evidence(
                id=chunk.id,
                title=f"{chunk.title} ({score:.0%})",
                text=f"Source: {chunk.source_path}\nPreview: {compact_preview(chunk.text, 1800)}",
            )
        )
    return evidence


def augment_case_with_index(case: Any, index_path: Path | None, top_k: int = 5) -> None:
    if not index_path:
        return
    extra = retrieve(index_path, f"{case.prompt}\n{case.output}", top_k=top_k)
    seen = {item.id for item in case.evidence}
    for item in extra:
        if item.id not in seen:
            case.evidence.append(item)
