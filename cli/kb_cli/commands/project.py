"""Project management command."""
import argparse

from kb_cli.client import KbClient


def register(subparsers):
    """Register project command."""
    p = subparsers.add_parser("project", help="Manage presales projects")
    sub = p.add_subparsers(dest="action", help="Project actions")

    # create
    create_p = sub.add_parser("create", help="Create a new project")
    create_p.add_argument("--customer", required=True, help="Customer name")
    create_p.add_argument("--industry", help="Industry")
    create_p.add_argument("--stage", default="draft", help="Stage (default: draft)")
    create_p.add_argument("--deployment-type", help="Deployment type")
    create_p.add_argument("--description", help="Description")
    create_p.add_argument("--owner", help="Owner")
    create_p.set_defaults(func=run_create)

    # list
    list_p = sub.add_parser("list", help="List projects")
    list_p.add_argument("--page", type=int, default=1, help="Page number")
    list_p.add_argument("--page-size", type=int, default=20, help="Page size")
    list_p.add_argument("--stage", help="Filter by stage")
    list_p.set_defaults(func=run_list)

    # get
    get_p = sub.add_parser("get", help="Get a project by ID")
    get_p.add_argument("project_id", help="Project ID")
    get_p.set_defaults(func=run_get)


def run_create(args: argparse.Namespace, client: KbClient) -> dict:
    """Create a new project."""
    data = {"customer_name": args.customer}
    if args.industry:
        data["industry"] = args.industry
    if args.stage:
        data["stage"] = args.stage
    if args.deployment_type:
        data["deployment_type"] = args.deployment_type
    if args.description:
        data["description"] = args.description
    if args.owner:
        data["owner"] = args.owner
    return client.post("/projects", json_data=data)


def run_list(args: argparse.Namespace, client: KbClient) -> dict:
    """List projects."""
    params = {"page": args.page, "page_size": args.page_size}
    if args.stage:
        params["stage"] = args.stage
    return client.get("/projects", params=params)


def run_get(args: argparse.Namespace, client: KbClient) -> dict:
    """Get a project by ID."""
    return client.get(f"/projects/{args.project_id}")
