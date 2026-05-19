"""Evidence management command."""
import argparse

from kb_cli.client import KbClient


def register(subparsers):
    """Register evidence command."""
    p = subparsers.add_parser("evidence", help="Manage evidence packs")
    sub = p.add_subparsers(dest="action", help="Evidence actions")

    # build
    build_p = sub.add_parser("build", help="Build evidence pack from card IDs")
    build_p.add_argument("--card-ids", required=True, help="Comma-separated card IDs")
    build_p.add_argument("--task-type", default="general", help="Task type (default: general)")
    build_p.add_argument("--project-id", help="Project ID")
    build_p.set_defaults(func=run_build)

    # list
    list_p = sub.add_parser("list", help="List evidence for a project")
    list_p.add_argument("--project-id", required=True, help="Project ID")
    list_p.set_defaults(func=run_list)

    # get
    get_p = sub.add_parser("get", help="Get a single evidence by ID")
    get_p.add_argument("evidence_id", help="Evidence ID")
    get_p.set_defaults(func=run_get)


def run_build(args: argparse.Namespace, client: KbClient) -> dict:
    """Build evidence pack."""
    data = {
        "card_ids": args.card_ids.split(","),
        "task_type": args.task_type,
    }
    if args.project_id:
        data["project_id"] = args.project_id
    return client.post("/evidence/build", json_data=data)


def run_list(args: argparse.Namespace, client: KbClient) -> dict:
    """List evidence for a project."""
    return client.get(f"/evidence/project/{args.project_id}")


def run_get(args: argparse.Namespace, client: KbClient) -> dict:
    """Get a single evidence."""
    return client.get(f"/evidence/{args.evidence_id}")
