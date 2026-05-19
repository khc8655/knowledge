"""Upload command — upload documents to kb-platform."""
import argparse
from pathlib import Path

from kb_cli.client import KbClient


def register(subparsers):
    """Register upload command."""
    p = subparsers.add_parser("upload", help="Upload a document to kb-platform")
    p.add_argument("file_path", help="Path to document file (.docx, .xlsx, .txt, .md, .pptx)")
    p.add_argument("--project-id", help="Associate with project ID")
    p.set_defaults(func=run)


def run(args: argparse.Namespace, client: KbClient) -> dict:
    """Upload a document."""
    path = Path(args.file_path)
    if not path.exists():
        return {"ok": False, "error": {"code": "FILE_NOT_FOUND", "message": f"File not found: {args.file_path}"}}

    kwargs = {}
    if args.project_id:
        kwargs["project_id"] = args.project_id

    return client.upload("/upload", args.file_path, **kwargs)
