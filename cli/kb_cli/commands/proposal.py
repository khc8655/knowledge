"""Proposal generation command."""
import argparse

from kb_cli.client import KbClient


def register(subparsers):
    """Register proposal command."""
    p = subparsers.add_parser("proposal", help="Generate proposals")
    sub = p.add_subparsers(dest="action", help="Proposal actions")

    # generate
    gen_p = sub.add_parser("generate", help="Generate a proposal")
    gen_p.add_argument("--project-id", required=True, help="Project ID")
    gen_p.add_argument("--title", required=True, help="Proposal title")
    gen_p.add_argument("--customer-context", help="Customer context")
    gen_p.add_argument("--industry", help="Industry")
    gen_p.add_argument("--deployment-type", help="Deployment type")
    gen_p.add_argument("--outline", help="Outline (newline-separated chapter titles)")
    gen_p.add_argument("--template-id", help="Template ID")
    gen_p.add_argument("--models", help="Comma-separated required models")
    gen_p.add_argument("--forbidden-models", help="Comma-separated forbidden models")
    gen_p.add_argument("--output-format", default="markdown", help="Output format")
    gen_p.set_defaults(func=run_generate)


def run_generate(args: argparse.Namespace, client: KbClient) -> dict:
    """Generate a proposal."""
    data = {
        "project_id": args.project_id,
        "title": args.title,
        "output_format": args.output_format,
    }
    if args.customer_context:
        data["customer_context"] = args.customer_context
    if args.industry:
        data["industry"] = args.industry
    if args.deployment_type:
        data["deployment_type"] = args.deployment_type
    if args.outline:
        data["outline"] = args.outline
    if args.template_id:
        data["template_id"] = args.template_id
    if args.models:
        data["required_models"] = args.models.split(",")
    if args.forbidden_models:
        data["forbidden_models"] = args.forbidden_models.split(",")
    return client.post("/proposals/generate", json_data=data, timeout=120)
