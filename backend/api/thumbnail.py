"""
PPT Thumbnail API — returns slide content as HTML preview.
"""
import json
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from db.models import get_db
from card.store import CardStore
from config import AppConfig

router = APIRouter(prefix="/thumbnails", tags=["thumbnails"])


@router.get("/{file_id}/{slide_num}")
async def get_slide_thumbnail(file_id: int, slide_num: int):
    """Return an HTML preview of a specific PPT slide."""
    cfg = AppConfig()
    data_dir = cfg.get("data_dir", os.environ.get("KB_DATA_DIR", "./data"))

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM uploaded_files WHERE id = ? AND file_type = 'ppt'",
            (file_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, detail="PPT_NOT_FOUND")
    finally:
        conn.close()

    # Find the card for this slide
    store = CardStore(data_dir=data_dir)
    cards = store.list_cards(source_type="ppt", page_size=500)

    target_card = None
    for card in cards.get("items", []):
        if card.get("slide_num") == slide_num:
            # Check if it belongs to the same file
            doc_file = row["original_name"]
            if card.get("doc_file") == doc_file or card.get("doc_file", "").endswith(doc_file):
                target_card = card
                break

    if not target_card:
        raise HTTPException(404, detail="SLIDE_NOT_FOUND")

    # Generate HTML preview
    title = target_card.get("title", f"第{slide_num}页")
    body = target_card.get("body", "")
    doc_file = target_card.get("doc_file", "")

    # Parse body into structured lines
    lines = body.split("\n")
    content_html = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if " | " in line:
            # Table row
            cells = line.split(" | ")
            row_html = "".join(f"<td>{_escape(c)}</td>" for c in cells)
            content_html += f"<tr>{row_html}</tr>"
        else:
            content_html += f"<p>{_escape(line)}</p>"

    # Check if we have table content
    has_table = any(" | " in line for line in lines if line.strip())

    table_html = ""
    if has_table:
        table_html = f"<table border='1' cellpadding='4' cellspacing='0'>{content_html}</table>"
        content_html = ""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{_escape(title)} - Slide {slide_num}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
               max-width: 800px; margin: 40px auto; padding: 20px;
               background: #f5f5f5; }}
        .slide {{ background: white; border-radius: 8px; padding: 30px;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #1a1a1a; font-size: 24px; border-bottom: 2px solid #3b82f6;
              padding-bottom: 10px; }}
        .meta {{ color: #666; font-size: 13px; margin-bottom: 20px; }}
        p {{ line-height: 1.6; color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .slide-num {{ display: inline-block; background: #3b82f6; color: white;
                      padding: 2px 10px; border-radius: 12px; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="slide">
        <div class="meta">
            <span class="slide-num">Slide {slide_num}</span>
            &nbsp; {_escape(doc_file)}
        </div>
        <h1>{_escape(title)}</h1>
        {content_html}
        {table_html}
    </div>
</body>
</html>"""

    return HTMLResponse(content=html)


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
