"""Output formatting for kb-cli."""
import json
import sys
from typing import Any


def is_tty() -> bool:
    """Check if stdout is a terminal."""
    return sys.stdout.isatty()


def format_output(result: dict[str, Any], force_json: bool = False, quiet: bool = False) -> str:
    """Format result for output.

    Args:
        result: {"ok": bool, "data": ..., "meta": {...}} or {"ok": False, "error": {...}}
        force_json: Force JSON output even in TTY
        quiet: Suppress non-JSON output
    """
    if quiet or force_json or not is_tty():
        return json.dumps(result, ensure_ascii=False, separators=(",", ":"))

    # Human-readable format for TTY
    if not result.get("ok"):
        err = result.get("error", {})
        lines = [f"Error: {err.get('message', 'Unknown error')}"]
        if err.get("hint"):
            lines.append(f"Hint: {err['hint']}")
        return "\n".join(lines)

    data = result.get("data")
    if data is None:
        return "OK"

    # Format based on data type
    if isinstance(data, dict):
        return _format_dict(data)
    elif isinstance(data, list):
        return _format_list(data)
    else:
        return str(data)


def _format_dict(data: dict) -> str:
    """Format a dict for human-readable output."""
    lines = []
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


def _format_list(data: list) -> str:
    """Format a list for human-readable output."""
    if not data:
        return "(empty)"

    lines = []
    for i, item in enumerate(data, 1):
        if isinstance(item, dict):
            # Try to find a title or name
            title = item.get("title") or item.get("name") or item.get("customer_name") or item.get("id", "")
            lines.append(f"{i}. {title}")
            for k, v in item.items():
                if k not in ("title", "name", "customer_name", "id"):
                    if isinstance(v, (dict, list)):
                        lines.append(f"   {k}: {json.dumps(v, ensure_ascii=False)}")
                    else:
                        lines.append(f"   {k}: {v}")
        else:
            lines.append(f"{i}. {item}")
    return "\n".join(lines)


def print_output(result: dict[str, Any], force_json: bool = False, quiet: bool = False):
    """Print formatted output to stdout."""
    print(format_output(result, force_json=force_json, quiet=quiet))


def print_error(message: str, hint: str | None = None):
    """Print error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)
    if hint:
        print(f"Hint: {hint}", file=sys.stderr)
