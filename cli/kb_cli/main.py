"""kb-cli main entry point."""
import argparse
import sys

from kb_cli.client import KbClient
from kb_cli.output import print_output


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="kb",
        description="kb-platform CLI for agent integration",
    )
    parser.add_argument("--json", action="store_true", help="Force JSON output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress non-JSON output")
    parser.add_argument("--api-url", help="Override API base URL")
    parser.add_argument("--timeout", type=int, help="Override request timeout (seconds)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register all command modules
    from kb_cli.commands import health, query, project, tender, evidence, proposal, reply, bom, chat, upload

    health.register(subparsers)
    query.register(subparsers)
    project.register(subparsers)
    tender.register(subparsers)
    evidence.register(subparsers)
    proposal.register(subparsers)
    reply.register(subparsers)
    bom.register(subparsers)
    chat.register(subparsers)
    upload.register(subparsers)

    return parser


def main() -> int:
    """Main entry point for kb-cli."""
    parser = create_parser()

    # First pass: extract global args and command
    # We need to handle global args that may appear after the subcommand
    argv = sys.argv[1:]

    # Extract global flags from anywhere in the args
    global_args = {
        "json": False,
        "quiet": False,
        "api_url": None,
        "timeout": None,
    }
    filtered_argv = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--json":
            global_args["json"] = True
        elif arg in ("--quiet", "-q"):
            global_args["quiet"] = True
        elif arg == "--api-url":
            global_args["api_url"] = argv[i + 1] if i + 1 < len(argv) else None
            i += 1
        elif arg == "--timeout":
            try:
                global_args["timeout"] = int(argv[i + 1]) if i + 1 < len(argv) else None
            except ValueError:
                pass
            i += 1
        else:
            filtered_argv.append(arg)
        i += 1

    # Parse remaining args with the parser
    args = parser.parse_args(filtered_argv)

    if not args.command:
        parser.print_help()
        return 1

    # Apply global args
    args.json = global_args["json"]
    args.quiet = global_args["quiet"]

    # Create client
    client = KbClient(base_url=global_args["api_url"], timeout=global_args["timeout"])

    # Get the handler function
    handler = getattr(args, "func", None)
    if handler is None:
        parser.print_help()
        return 1

    # Run the command
    try:
        result = handler(args, client)
        if result is not None:
            print_output(result, force_json=args.json, quiet=args.quiet)
            return 0 if result.get("ok", False) else 1
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        if args.json:
            print_output({"ok": False, "error": {"code": "UNKNOWN", "message": str(e)}},
                         force_json=True)
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
