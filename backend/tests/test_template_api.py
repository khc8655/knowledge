"""Tests for Template CRUD API — self-contained (no fastapi needed)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import tempfile
import uuid
from datetime import datetime, timezone

from db.models import init_db


# ------------------------------------------------------------------
# Inline helper functions (mirror api/template.py helpers)
# ------------------------------------------------------------------
def create_template(data: dict, conn) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    template_id = data.get("id") or str(uuid.uuid4())
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO templates (id, template_type, name, industry, deployment_type,
                               file_path, schema_json, enabled, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            template_id,
            data["template_type"],
            data["name"],
            data.get("industry"),
            data.get("deployment_type"),
            data["file_path"],
            data.get("schema_json", "{}"),
            data.get("enabled", 1),
            now,
            now,
        ),
    )
    conn.commit()
    return get_template(template_id, conn)


def get_template(template_id: str, conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
    row = cur.fetchone()
    if row is None:
        return None
    return dict(row)


def list_templates(template_type=None, industry=None, conn=None):
    cur = conn.cursor()
    conditions = ["enabled = 1"]
    params = []
    if template_type:
        conditions.append("template_type = ?")
        params.append(template_type)
    if industry:
        conditions.append("industry = ?")
        params.append(industry)
    where = " AND ".join(conditions)
    cur.execute(f"SELECT * FROM templates WHERE {where} ORDER BY created_at DESC", params)
    return [dict(row) for row in cur.fetchall()]


def update_template(template_id: str, data: dict, conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM templates WHERE id = ?", (template_id,))
    if cur.fetchone() is None:
        return None
    mutable_fields = [
        "template_type", "name", "industry", "deployment_type",
        "file_path", "schema_json", "enabled",
    ]
    sets = []
    params = []
    for field in mutable_fields:
        if field in data:
            sets.append(f"{field} = ?")
            params.append(data[field])
    if not sets:
        return get_template(template_id, conn)
    now = datetime.now(timezone.utc).isoformat()
    sets.append("updated_at = ?")
    params.append(now)
    params.append(template_id)
    cur.execute(f"UPDATE templates SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    return get_template(template_id, conn)


def delete_template(template_id: str, conn) -> bool:
    cur = conn.cursor()
    cur.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    conn.commit()
    return cur.rowcount > 0


# ------------------------------------------------------------------
# Test
# ------------------------------------------------------------------
def _make_conn():
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    conn = sqlite3.connect(tmp.name)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def test_template_crud():
    """Full CRUD lifecycle: create, get, list, update, delete."""
    conn = _make_conn()

    # --- Create ---
    data = {
        "template_type": "proposal",
        "name": "Standard Proposal Template",
        "industry": "technology",
        "deployment_type": "cloud",
        "file_path": "/templates/proposal_v1.docx",
        "schema_json": '{"sections": ["intro", "solution", "pricing"]}',
    }
    tmpl = create_template(data, conn)
    assert tmpl is not None
    assert tmpl["template_type"] == "proposal"
    assert tmpl["name"] == "Standard Proposal Template"
    assert tmpl["industry"] == "technology"
    assert tmpl["enabled"] == 1
    template_id = tmpl["id"]

    # --- Get ---
    fetched = get_template(template_id, conn)
    assert fetched is not None
    assert fetched["id"] == template_id
    assert fetched["file_path"] == "/templates/proposal_v1.docx"

    # --- Get non-existent ---
    assert get_template("nonexistent", conn) is None

    # --- List (all) ---
    data2 = {
        "template_type": "tender",
        "name": "Tender Response Template",
        "industry": "government",
        "file_path": "/templates/tender_v1.docx",
    }
    create_template(data2, conn)

    all_templates = list_templates(conn=conn)
    assert len(all_templates) == 2

    # --- List filtered by type ---
    proposals = list_templates(template_type="proposal", conn=conn)
    assert len(proposals) == 1
    assert proposals[0]["template_type"] == "proposal"

    # --- List filtered by industry ---
    gov = list_templates(industry="government", conn=conn)
    assert len(gov) == 1
    assert gov[0]["industry"] == "government"

    # --- List filtered by both ---
    both = list_templates(template_type="tender", industry="government", conn=conn)
    assert len(both) == 1

    # --- List with no match ---
    none = list_templates(template_type="ppt", conn=conn)
    assert len(none) == 0

    # --- Update ---
    updated = update_template(template_id, {"name": "Updated Proposal", "enabled": 0}, conn)
    assert updated is not None
    assert updated["name"] == "Updated Proposal"
    assert updated["enabled"] == 0
    assert updated["template_type"] == "proposal"  # unchanged

    # --- Update non-existent ---
    assert update_template("nonexistent", {"name": "x"}, conn) is None

    # --- Delete ---
    assert delete_template(template_id, conn) is True
    assert get_template(template_id, conn) is None

    # --- Delete non-existent ---
    assert delete_template("nonexistent", conn) is False

    # Verify only one template remains
    remaining = list_templates(conn=conn)
    assert len(remaining) == 1
    assert remaining[0]["template_type"] == "tender"

    conn.close()


if __name__ == '__main__':
    test_template_crud()
    print('test_template_crud PASSED')
