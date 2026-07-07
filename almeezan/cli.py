from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .batch import run_batch
from .core import evaluate_case
from .evidence import augment_case_with_index, build_index
from .gate import gate_case
from .ledger import DEFAULT_LEDGER, verify_ledger
from .models import EvaluationCase
from .reports import gate_to_markdown, result_to_markdown


def _load_case(path: Path) -> EvaluationCase:
    data = json.loads(path.read_text(encoding="utf-8"))
    return EvaluationCase.from_dict(data, base_dir=str(path.parent))


def evaluate_command(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    case = _load_case(input_path)
    augment_case_with_index(case, Path(args.evidence_index) if args.evidence_index else None, top_k=args.top_k)
    result = evaluate_case(case, ledger_path=Path(args.ledger), write_ledger=not args.no_ledger)
    if args.format == "json":
        payload = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    else:
        payload = result_to_markdown(result)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
        print(str(out_path.resolve()))
    else:
        print(payload)
    return 2 if result.verdict == "BLOCK" and args.fail_on_block else 0


def gate_command(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    case = _load_case(input_path)
    augment_case_with_index(case, Path(args.evidence_index) if args.evidence_index else None, top_k=args.top_k)
    result = gate_case(case, ledger_path=args.ledger, write_ledger=not args.no_ledger)
    if args.format == "json":
        payload = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    else:
        payload = gate_to_markdown(result)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
        print(str(out_path.resolve()))
    else:
        print(payload)
    return 2 if args.fail_on_block and result.action == "block" else 0


def verify_command(args: argparse.Namespace) -> int:
    result = verify_ledger(args.ledger)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def index_command(args: argparse.Namespace) -> int:
    extensions = {item if item.startswith(".") else f".{item}" for item in args.extensions.split(",") if item.strip()}
    payload = build_index(Path(args.source), Path(args.out), extensions=extensions)
    print(json.dumps({key: payload[key] for key in ("source", "file_count", "chunk_count")}, ensure_ascii=False, indent=2))
    return 0


def batch_command(args: argparse.Namespace) -> int:
    summary = run_batch(
        input_dir=Path(args.input_dir),
        out_dir=Path(args.out_dir),
        evidence_index=Path(args.evidence_index) if args.evidence_index else None,
        top_k=args.top_k,
        write_ledger=not args.no_ledger,
        ledger_path=args.ledger,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 2 if args.fail_on_block and summary.get("verdicts", {}).get("BLOCK") else 0


def web_command(args: argparse.Namespace) -> int:
    from .web import run_server

    run_server(host=args.host, port=args.port, ledger=args.ledger, evidence_index=args.evidence_index, top_k=args.top_k)
    return 0


def version_command(args: argparse.Namespace) -> int:
    from .version import __version__

    print(json.dumps({"service": "almeezan", "version": __version__}, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="almeezan", description="Local AI output judge.")
    sub = parser.add_subparsers(dest="command", required=True)

    evaluate = sub.add_parser("evaluate", help="Evaluate one model output from a JSON case file.")
    evaluate.add_argument("--input", required=True, help="Path to input JSON case.")
    evaluate.add_argument("--out", help="Optional output report path.")
    evaluate.add_argument("--format", choices=["md", "json"], default="md")
    evaluate.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    evaluate.add_argument("--evidence-index", help="Optional local evidence index JSON.")
    evaluate.add_argument("--top-k", type=int, default=5, help="Evidence chunks to retrieve from index.")
    evaluate.add_argument("--no-ledger", action="store_true")
    evaluate.add_argument("--fail-on-block", action="store_true")
    evaluate.set_defaults(func=evaluate_command)

    gate = sub.add_parser("gate", help="Evaluate, redact/rewrite, and return an allow/review/block action.")
    gate.add_argument("--input", required=True, help="Path to input JSON case.")
    gate.add_argument("--out", help="Optional output gate report path.")
    gate.add_argument("--format", choices=["md", "json"], default="json")
    gate.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    gate.add_argument("--evidence-index", help="Optional local evidence index JSON.")
    gate.add_argument("--top-k", type=int, default=5, help="Evidence chunks to retrieve from index.")
    gate.add_argument("--no-ledger", action="store_true")
    gate.add_argument("--fail-on-block", action="store_true")
    gate.set_defaults(func=gate_command)

    index = sub.add_parser("index", help="Build a local evidence index from a file or directory.")
    index.add_argument("--source", required=True, help="Source file or directory.")
    index.add_argument("--out", default="data/evidence_index.json", help="Output index JSON path.")
    index.add_argument("--extensions", default="md,txt,json,jsonl,yml,yaml,html,htm,csv")
    index.set_defaults(func=index_command)

    batch = sub.add_parser("batch", help="Evaluate every JSON case in a directory.")
    batch.add_argument("--input-dir", required=True)
    batch.add_argument("--out-dir", default="reports/batch")
    batch.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    batch.add_argument("--evidence-index", help="Optional local evidence index JSON.")
    batch.add_argument("--top-k", type=int, default=5)
    batch.add_argument("--no-ledger", action="store_true")
    batch.add_argument("--fail-on-block", action="store_true")
    batch.set_defaults(func=batch_command)

    verify = sub.add_parser("verify-ledger", help="Verify the tamper-evident ledger.")
    verify.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    verify.set_defaults(func=verify_command)

    web = sub.add_parser("web", help="Run the local web interface.")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8787)
    web.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    web.add_argument("--evidence-index", help="Optional default evidence index JSON.")
    web.add_argument("--top-k", type=int, default=5)
    web.set_defaults(func=web_command)

    version = sub.add_parser("version", help="Print service version.")
    version.set_defaults(func=version_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
