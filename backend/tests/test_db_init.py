import sqlite3
import tempfile
import os
import pytest


def test_init_db_creates_all_tables():
    """init_db should create all v7.5 tables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from db.models import init_db
        init_db(conn)

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row['name'] for row in cursor.fetchall()}

        expected = {
            'uploaded_files', 'jobs', 'query_feedback',
            'route_mappings', 'route_cache',
            'evidence_packs', 'presales_projects',
            'project_requirements', 'project_outputs',
            'project_evidence_links', 'project_feedback',
            'templates',
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"
        conn.close()
