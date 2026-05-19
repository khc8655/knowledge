"""Chat command — conversational AI sessions."""
import argparse
import json

from kb_cli.client import KbClient


def register(subparsers):
    """Register chat command."""
    p = subparsers.add_parser("chat", help="Conversational AI sessions")
    sub = p.add_subparsers(dest="action", help="Chat actions")

    # create
    create_p = sub.add_parser("create", help="Create a new chat session")
    create_p.add_argument("--title", help="Session title")
    create_p.add_argument("--mode", default="auto",
                          choices=["auto", "search", "proposal", "tender", "bom", "reply"],
                          help="Mode (default: auto)")
    create_p.set_defaults(func=run_create)

    # list
    list_p = sub.add_parser("list", help="List chat sessions")
    list_p.add_argument("--status", default="active", help="Filter by status (default: active)")
    list_p.add_argument("--page", type=int, default=1, help="Page number")
    list_p.add_argument("--page-size", type=int, default=50, help="Page size")
    list_p.set_defaults(func=run_list)

    # get
    get_p = sub.add_parser("get", help="Get a session with messages")
    get_p.add_argument("session_id", help="Session ID")
    get_p.set_defaults(func=run_get)

    # send
    send_p = sub.add_parser("send", help="Send a message to a session")
    send_p.add_argument("session_id", help="Session ID")
    send_p.add_argument("content", help="Message content")
    send_p.add_argument("--mode-override", help="Override session mode for this message")
    send_p.add_argument("--stream", action="store_true", help="Stream SSE events as JSONL")
    send_p.set_defaults(func=run_send)


def run_create(args: argparse.Namespace, client: KbClient) -> dict:
    """Create a new chat session."""
    data = {"mode": args.mode}
    if args.title:
        data["title"] = args.title
    return client.post("/chat/sessions", json_data=data)


def run_list(args: argparse.Namespace, client: KbClient) -> dict:
    """List chat sessions."""
    params = {"status": args.status, "page": args.page, "page_size": args.page_size}
    return client.get("/chat/sessions", params=params)


def run_get(args: argparse.Namespace, client: KbClient) -> dict:
    """Get a session with messages."""
    return client.get(f"/chat/sessions/{args.session_id}")


def run_send(args: argparse.Namespace, client: KbClient) -> dict:
    """Send a message to a chat session."""
    data = {"content": args.content}
    if args.mode_override:
        data["mode_override"] = args.mode_override

    if args.stream:
        # Stream SSE events as JSONL
        for event_type, event_data in client.post_stream(
            f"/chat/sessions/{args.session_id}/messages",
            json_data=data
        ):
            print(json.dumps({"event": event_type, "data": event_data}, ensure_ascii=False))
        return None  # Already printed
    else:
        # Accumulate full response
        full_content = ""
        cards = []
        for event_type, event_data in client.post_stream(
            f"/chat/sessions/{args.session_id}/messages",
            json_data=data
        ):
            if event_type == "text":
                full_content += event_data.get("delta", "")
            elif event_type == "cards":
                cards = event_data.get("cards", [])
            elif event_type == "error":
                return {"ok": False, "error": event_data}

        return {
            "ok": True,
            "data": {
                "content": full_content,
                "cards": cards,
            },
        }
