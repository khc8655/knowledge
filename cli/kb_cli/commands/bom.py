"""BOM generation command."""
import argparse

from kb_cli.client import KbClient


def register(subparsers):
    """Register bom command."""
    p = subparsers.add_parser("bom", help="Generate BOM (Bill of Materials)")
    sub = p.add_subparsers(dest="action", help="BOM actions")

    # generate
    gen_p = sub.add_parser("generate", help="Generate a BOM")
    gen_p.add_argument("--project-id", required=True, help="Project ID")
    gen_p.add_argument("--scenario", default="", help="Use-case scenario")
    gen_p.add_argument("--room-count", type=int, default=1, help="Number of rooms/endpoints")
    gen_p.add_argument("--deployment-type", default="on-prem", choices=["cloud", "on-prem"],
                       help="Deployment type (default: on-prem)")
    gen_p.add_argument("--models", help="Comma-separated required models")
    gen_p.add_argument("--budget-limit", type=float, help="Budget limit (0 = no limit)")
    gen_p.set_defaults(func=run_generate)


def run_generate(args: argparse.Namespace, client: KbClient) -> dict:
    """Generate a BOM."""
    data = {
        "project_id": args.project_id,
        "scenario": args.scenario,
        "room_count": args.room_count,
        "deployment_type": args.deployment_type,
    }
    if args.models:
        data["required_models"] = args.models.split(",")
    if args.budget_limit:
        data["budget_limit"] = args.budget_limit
    return client.post("/bom/generate", json_data=data, timeout=120)
