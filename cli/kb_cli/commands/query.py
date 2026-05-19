"""Query command — search the knowledge base."""
import argparse

from kb_cli.client import KbClient


def register(subparsers):
    """Register query command."""
    p = subparsers.add_parser("query", help="Search the knowledge base")
    p.add_argument("query_text", help="Search query (max 500 chars)")
    p.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    p.set_defaults(func=run)


def run(args: argparse.Namespace, client: KbClient) -> dict:
    """Run knowledge base search."""
    return client.post("/query", json_data={"query": args.query_text, "limit": args.limit})
