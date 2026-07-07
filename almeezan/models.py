from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Evidence:
    id: str
    title: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "title": self.title, "text": self.text}


@dataclass
class EvaluationCase:
    prompt: str
    output: str
    evidence: list[Evidence] = field(default_factory=list)
    evidence_paths: list[str] = field(default_factory=list)
    model: str = "unknown"
    use_case: str = "general"
    risk_level: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any], base_dir: str | None = None) -> "EvaluationCase":
        evidence = []
        for index, item in enumerate(data.get("evidence", []), start=1):
            if isinstance(item, str):
                evidence.append(Evidence(id=f"evidence-{index}", title=f"Evidence {index}", text=item))
            elif isinstance(item, dict):
                evidence.append(
                    Evidence(
                        id=str(item.get("id") or f"evidence-{index}"),
                        title=str(item.get("title") or item.get("id") or f"Evidence {index}"),
                        text=str(item.get("text") or ""),
                    )
                )

        paths = [str(path) for path in data.get("evidence_paths", [])]
        if paths:
            from pathlib import Path

            root = Path(base_dir or ".").resolve()
            for index, raw_path in enumerate(paths, start=1):
                path = Path(raw_path)
                if not path.is_absolute():
                    path = root / path
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    text = path.read_text(encoding="utf-8-sig")
                evidence.append(Evidence(id=f"path-{index}", title=str(path), text=text))

        return cls(
            prompt=str(data.get("prompt") or ""),
            output=str(data.get("output") or ""),
            evidence=evidence,
            evidence_paths=paths,
            model=str(data.get("model") or "unknown"),
            use_case=str(data.get("use_case") or "general"),
            risk_level=str(data.get("risk_level") or "medium"),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_redacted_dict(self) -> dict[str, Any]:
        from .pii import redact_text

        return {
            "prompt": redact_text(self.prompt),
            "output": redact_text(self.output),
            "evidence": [
                {"id": item.id, "title": item.title, "text_preview": redact_text(item.text[:600])}
                for item in self.evidence
            ],
            "model": self.model,
            "use_case": self.use_case,
            "risk_level": self.risk_level,
            "metadata": self.metadata,
        }


@dataclass
class Finding:
    code: str
    title: str
    severity: str
    detail: str
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "severity": self.severity,
            "detail": self.detail,
            "evidence": self.evidence,
        }


@dataclass
class Signal:
    name: str
    score: float
    status: str
    summary: str
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 2),
            "status": self.status,
            "summary": self.summary,
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass
class EvaluationResult:
    id: str
    created_at: str
    score: float
    verdict: str
    decision: str
    signals: list[Signal]
    case: EvaluationCase
    ledger: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "score": round(self.score, 2),
            "verdict": self.verdict,
            "decision": self.decision,
            "signals": [signal.to_dict() for signal in self.signals],
            "case": self.case.to_redacted_dict(),
            "ledger": self.ledger,
        }

