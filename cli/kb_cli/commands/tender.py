"""Tender analysis command."""
import argparse
from pathlib import Path

from kb_cli.client import KbClient


def register(subparsers):
    """Register tender command."""
    p = subparsers.add_parser("tender", help="Analyze tender documents")
    sub = p.add_subparsers(dest="action", help="Tender actions")

    # analyze
    analyze_p = sub.add_parser("analyze", help="Analyze tender text and extract requirements")
    analyze_p.add_argument("--text", help="Tender text content")
    analyze_p.add_argument("--text-file", help="Path to tender text file")
    analyze_p.add_argument("--project-id", help="Project ID (persists requirements if provided)")
    analyze_p.set_defaults(func=run_analyze)

    # match
    match_p = sub.add_parser("match", help="Match requirements against knowledge base")
    match_p.add_argument("--project-id", help="Project ID")
    match_p.add_argument("--requirement-ids", help="Comma-separated requirement IDs")
    match_p.add_argument("--candidate-models", help="Comma-separated candidate models")
    match_p.set_defaults(func=run_match)


def run_analyze(args: argparse.Namespace, client: KbClient) -> dict:
    """Analyze tender text."""
    text = args.text
    if not text and args.text_file:
        path = Path(args.text_file)
        if not path.exists():
            return {"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": f"File not found: {args.text_file}"}}
        text = path.read_text(encoding="utf-8")
    if not text:
        return {"ok": False, "error": {"code": "NO_INPUT", "message": "Provide --text or --text-file"}}

    data = {"tender_text": text}
    if args.project_id:
        data["project_id"] = args.project_id
    return client.post("/tender/analyze", json_data=data)


def run_match(args: argparse.Namespace, client: KbClient) -> dict:
    """Match requirements against knowledge base."""
    data = {}
    if args.project_id:
        data["project_id"] = args.project_id
    if args.requirement_ids:
        data["requirement_ids"] = args.requirement_ids.split(",")
    if args.candidate_models:
        data["candidate_models"] = args.candidate_models.split(",")
    if not data.get("project_id") and not data.get("requirement_ids"):
        return {"ok": False, "error": {"code": "NO_INPUT", "message": "Provide --project-id or --requirement-ids"}}
    return client.post("/tender/match", json_data=data)
