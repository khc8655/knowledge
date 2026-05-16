import uuid
import json
from datetime import datetime, timezone


class OutputService:
    def __init__(self, conn):
        self.conn = conn

    def create_output(self, project_id, output_type, title, content_md=None, content_json=None):
        """Create output with uuid id, version=1, status='draft'. Return dict."""
        output_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        content_json_str = json.dumps(content_json) if content_json is not None else '{}'

        self.conn.execute(
            """INSERT INTO project_outputs
               (id, project_id, output_type, title, status, content_md, content_json,
                version, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'draft', ?, ?, 1, ?, ?)""",
            (output_id, project_id, output_type, title, content_md, content_json_str, now, now),
        )
        self.conn.commit()

        return {
            'id': output_id,
            'project_id': project_id,
            'output_type': output_type,
            'title': title,
            'status': 'draft',
            'content_md': content_md,
            'content_json': content_json or {},
            'version': 1,
            'created_at': now,
            'updated_at': now,
        }

    def get_output(self, output_id):
        """Get by id. Parse content_json from str to dict."""
        row = self.conn.execute(
            "SELECT * FROM project_outputs WHERE id = ?", (output_id,)
        ).fetchone()
        if row is None:
            return None

        result = dict(row)
        try:
            result['content_json'] = json.loads(result.get('content_json') or '{}')
        except (json.JSONDecodeError, TypeError):
            result['content_json'] = {}
        return result

    def list_outputs(self, project_id, output_type=None):
        """List for project, optional type filter."""
        if output_type is not None:
            rows = self.conn.execute(
                "SELECT * FROM project_outputs WHERE project_id = ? AND output_type = ? ORDER BY created_at DESC",
                (project_id, output_type),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM project_outputs WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,),
            ).fetchall()

        results = []
        for row in rows:
            r = dict(row)
            try:
                r['content_json'] = json.loads(r.get('content_json') or '{}')
            except (json.JSONDecodeError, TypeError):
                r['content_json'] = {}
            results.append(r)
        return results

    def update_output(self, output_id, content_md=None, content_json=None, title=None):
        """Update fields, increment version."""
        existing = self.get_output(output_id)
        if existing is None:
            return None

        now = datetime.now(timezone.utc).isoformat()
        new_version = existing['version'] + 1

        updates = []
        params = []

        if content_md is not None:
            updates.append("content_md = ?")
            params.append(content_md)
        if content_json is not None:
            updates.append("content_json = ?")
            params.append(json.dumps(content_json))
        if title is not None:
            updates.append("title = ?")
            params.append(title)

        if not updates:
            return existing

        updates.append("version = ?")
        params.append(new_version)
        updates.append("updated_at = ?")
        params.append(now)

        params.append(output_id)
        self.conn.execute(
            f"UPDATE project_outputs SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        self.conn.commit()

        return self.get_output(output_id)

    def update_status(self, output_id, status):
        """Update status field."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE project_outputs SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, output_id),
        )
        self.conn.commit()

    def link_evidence(self, project_id, output_id, evidence_id, target_path, link_role='primary'):
        """Insert into project_evidence_links."""
        link_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        self.conn.execute(
            """INSERT INTO project_evidence_links
               (id, project_id, output_id, evidence_id, target_path, link_role, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (link_id, project_id, output_id, evidence_id, target_path, link_role, now),
        )
        self.conn.commit()

        return {
            'id': link_id,
            'project_id': project_id,
            'output_id': output_id,
            'evidence_id': evidence_id,
            'target_path': target_path,
            'link_role': link_role,
            'created_at': now,
        }

    def get_evidence_links(self, output_id):
        """Get all evidence links for output."""
        rows = self.conn.execute(
            "SELECT * FROM project_evidence_links WHERE output_id = ? ORDER BY created_at",
            (output_id,),
        ).fetchall()
        return [dict(row) for row in rows]
