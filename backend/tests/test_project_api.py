"""Tests for project CRUD helpers using a temp SQLite database."""
import os
import sqlite3
import tempfile

import pytest

# Ensure the backend package is importable
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.models import init_db
from api.project import create_project, get_project, list_projects, update_project, archive_project


@pytest.fixture()
def conn():
    """Yield a fresh temp-DB connection with schema initialised."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    init_db(c)
    yield c
    c.close()
    os.unlink(path)


def test_create_and_get_project(conn):
    proj = create_project({"customer_name": "Acme Corp", "industry": "tech"}, conn)
    assert proj["customer_name"] == "Acme Corp"
    assert proj["stage"] == "draft"
    assert proj["id"]

    fetched = get_project(proj["id"], conn)
    assert fetched is not None
    assert fetched["customer_name"] == "Acme Corp"

    assert get_project("nonexistent", conn) is None


def test_list_projects(conn):
    for i in range(3):
        create_project({"customer_name": f"Customer {i}"}, conn)

    result = list_projects(conn=conn)
    assert result["total"] == 3
    assert len(result["items"]) == 3

    # Pagination
    page1 = list_projects(page=1, page_size=2, conn=conn)
    assert page1["total"] == 3
    assert len(page1["items"]) == 2

    # Stage filter
    create_project({"customer_name": "Special", "stage": "won"}, conn)
    filtered = list_projects(stage="won", conn=conn)
    assert filtered["total"] == 1
    assert filtered["items"][0]["customer_name"] == "Special"


def test_archive_project(conn):
    proj = create_project({"customer_name": "Doomed Inc"}, conn)
    assert archive_project(proj["id"], conn) is True

    # Archived project should not appear in list
    result = list_projects(conn=conn)
    assert result["total"] == 0

    # But get_project still returns it
    fetched = get_project(proj["id"], conn)
    assert fetched is not None
    assert fetched["archived_at"] is not None

    # Archiving nonexistent returns False
    assert archive_project("nonexistent", conn) is False
