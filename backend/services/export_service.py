"""Export Service — exports project outputs to files with evidence index."""
import os
import json
from datetime import datetime, timezone
from services.output_service import OutputService


class ExportService:
    def __init__(self, conn, data_dir=None):
        self.conn = conn
        self.data_dir = data_dir or os.environ.get('KB_DATA_DIR', './data')
        self._export_dir = os.path.join(self.data_dir, 'exports')
        os.makedirs(self._export_dir, exist_ok=True)

    def export(self, output_id, fmt='markdown'):
        svc = OutputService(self.conn)
        output = svc.get_output(output_id)
        if not output:
            raise ValueError(f"Output not found: {output_id}")

        current_version = output.get('version') or 1
        next_version = current_version + 1
        now = datetime.now(timezone.utc).isoformat()

        links = svc.get_evidence_links(output_id)
        evidence_index = self._build_evidence_index(links)

        if fmt == 'json':
            export_content = self._export_json(output, evidence_index, current_version)
            ext = 'json'
        else:
            export_content = self._export_markdown(output, evidence_index, current_version)
            ext = 'md'

        filename = f"{output_id}_v{current_version}.{ext}"
        export_path = os.path.join(self._export_dir, filename)
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(export_content)

        self.conn.execute(
            "UPDATE project_outputs SET version=?, export_path=?, status='exported', updated_at=? WHERE id=?",
            (next_version, export_path, now, output_id)
        )
        self.conn.commit()

        return {
            'output_id': output_id,
            'export_path': export_path,
            'version': current_version,
            'format': fmt,
        }

    def _build_evidence_index(self, links):
        index = {}
        for link in links:
            eid = link.get('evidence_id', '')
            if eid not in index:
                index[eid] = {
                    'evidence_id': eid,
                    'target_paths': [],
                    'role': link.get('link_role', 'primary'),
                }
            index[eid]['target_paths'].append(link.get('target_path', ''))
        return list(index.values())

    def _export_markdown(self, output, evidence_index, version):
        lines = []
        lines.append(f"# {output.get('title', '未命名')}")
        lines.append(f"\n> 版本: v{version} | 导出时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} | 状态: {output.get('status', 'draft')}")
        lines.append('')
        content_md = output.get('content_md', '')
        if content_md:
            lines.append(content_md)
            lines.append('')
        lines.append('---')
        lines.append(f'## 证据索引 (共 {len(evidence_index)} 条)')
        lines.append('')
        if evidence_index:
            for i, ev in enumerate(evidence_index, 1):
                paths = ', '.join(ev.get('target_paths', []))
                lines.append(f"{i}. **{ev['evidence_id']}** — 关联: {paths} ({ev.get('role', 'primary')})")
        else:
            lines.append('暂无关联证据。')
        lines.append('')
        lines.append(f'---\n*v{version} | Exported by KB Platform v7.5*')
        return '\n'.join(lines)

    def _export_json(self, output, evidence_index, version):
        data = {
            'output_id': output.get('id'),
            'title': output.get('title'),
            'output_type': output.get('output_type'),
            'status': output.get('status'),
            'version': version,
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'content_md': output.get('content_md'),
            'content_json': output.get('content_json', {}),
            'evidence_index': evidence_index,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
