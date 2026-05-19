"""Reply generation command."""
import argparse

from kb_cli.client import KbClient


def register(subparsers):
    """Register reply command."""
    p = subparsers.add_parser("reply", help="Generate customer replies")
    sub = p.add_subparsers(dest="action", help="Reply actions")

    # generate
    gen_p = sub.add_parser("generate", help="Generate a customer reply")
    gen_p.add_argument("--question", required=True, help="Customer question")
    gen_p.add_argument("--project-id", default="default", help="Project ID (default: default)")
    gen_p.add_argument("--keywords", help="Comma-separated keywords (auto-extracted if omitted)")
    gen_p.add_argument("--tone", default="neutral", choices=["neutral", "formal", "friendly"],
                       help="Tone (default: neutral)")
    gen_p.add_argument("--max-chars", type=int, default=2000, help="Max characters (default: 2000)")
    gen_p.set_defaults(func=run_generate)


def run_generate(args: argparse.Namespace, client: KbClient) -> dict:
    """Generate a customer reply."""
    data = {
        "customer_question": args.question,
        "project_id": args.project_id,
        "tone": args.tone,
        "max_chars": args.max_chars,
    }
    if args.keywords:
        data["keywords"] = args.keywords.split(",")
    return client.post("/reply/generate", json_data=data, timeout=120)
