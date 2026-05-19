"""Health check command."""
import argparse

from kb_cli.client import KbClient


def register(subparsers):
    """Register health command."""
    p = subparsers.add_parser("health", help="Check kb-platform health status")
    p.set_defaults(func=run)


def run(args: argparse.Namespace, client: KbClient) -> dict:
    """Run health check."""
    return client.get("/health")
