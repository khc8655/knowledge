# Export & Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add export functionality (Markdown/JSON) with evidence index and version tracking, plus remaining PSA test cases.

**Architecture:** Export service takes an output (proposal/tender/bom/reply), enriches it with evidence links and version info, writes to file, and updates output status to 'exported'. PSA tests validate the full pre-sales workflow.

**Tech Stack:** Python 3, FastAPI, SQLite

---

## File Structure

**New files:**
- `backend/services/export_service.py` — Export logic: generate markdown/JSON with evidence index
- `backend/api/export.py` — Export endpoint: POST /exports/{output_id}
- `backend/tests/test_export_service.py` — Export service tests
- `backend/tests/test_psa_cases.py` — PSA01-PSA08 test cases

---

### Task 1: Export Service and API

**Files:**
- Create: `backend/services/export_service.py`
- Create: `backend/api/export.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_export_service.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_export_service.py
import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_export_proposal_markdown():
    """Export generates markdown with evidence index."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.output_service import OutputService
        from services.export_service import ExportService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = OutputService(conn)
        output = svc.create_output('proj-001', 'proposal', '测试方案',
            content_md='# 测试方案\n## 第一章\n内容',
            content_json={'chapters': [{'title': '第一章', 'evidence_ids': ['ev-001']}]})
        exp = ExportService(conn, data_dir=tmpdir)
        result = exp.export(output['id'], fmt='markdown')
        assert result['export_path'] is not None
        assert result['version'] == 1
        assert os.path.exists(result['export_path'])
        with open(result['export_path'], 'r') as f:
            content = f.read()
        assert '证据索引' in content
        conn.close()

def test_export_version_increment():
    """Repeated exports increment version."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.output_service import OutputService
        from services.export_service import ExportService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = OutputService(conn)
        output = svc.create_output('proj-001', 'bom', 'BOM清单',
            content_md='# BOM\n产品列表')
        exp = ExportService(conn, data_dir=tmpdir)
        r1 = exp.export(output['id'], fmt='markdown')
        assert r1['version'] == 1
        r2 = exp.export(output['id'], fmt='markdown')
        assert r2['version'] == 2
        conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "import sys; sys.path.insert(0,'.'); exec(open('tests/test_export_service.py').read()); test_export_proposal_markdown(); print('OK')"`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# backend/services/export_service.py
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
        """Export an output to file with evidence index and version tracking.

        Args:
            output_id: The output to export.
            fmt: Export format — 'markdown' or 'json'.

        Returns:
            Dict with: export_path, version, format, output_id.
        """
        svc = OutputService(self.conn)
        output = svc.get_output(output_id)
        if not output:
            raise ValueError(f"Output not found: {output_id}")

        # Increment version
        new_version = (output.get('version') or 1) + 1
        now = datetime.now(timezone.utc).isoformat()

        # Gather evidence links
        links = svc.get_evidence_links(output_id)
        evidence_index = self._build_evidence_index(links)

        # Generate export content
        if fmt == 'json':
            export_content = self._export_json(output, evidence_index, new_version)
            ext = 'json'
        else:
            export_content = self._export_markdown(output, evidence_index, new_version)
            ext = 'md'

        # Write to file
        filename = f"{output_id}_v{new_version}.{ext}"
        export_path = os.path.join(self._export_dir, filename)
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(export_content)

        # Update output: version, export_path, status -> exported
        self.conn.execute(
            "UPDATE project_outputs SET version=?, export_path=?, status='exported', updated_at=? WHERE id=?",
            (new_version, export_path, now, output_id)
        )
        self.conn.commit()

        return {
            'output_id': output_id,
            'export_path': export_path,
            'version': new_version,
            'format': fmt,
        }

    def _build_evidence_index(self, links):
        """Build evidence index from links."""
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
        """Generate markdown export with metadata and evidence index."""
        lines = []
        lines.append(f"# {output.get('title', '未命名')}")
        lines.append(f"\n> 版本: v{version} | 导出时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} | 状态: {output.get('status', 'draft')}")
        lines.append('')

        # Main content
        content_md = output.get('content_md', '')
        if content_md:
            lines.append(content_md)
            lines.append('')

        # Evidence index
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
        """Generate JSON export with full metadata."""
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
```

- [ ] **Step 4: Create API**

```python
# backend/api/export.py
from fastapi import APIRouter, HTTPException
from db.models import get_db
from services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/{output_id}")
async def export_output(output_id: str, body: dict = None):
    body = body or {}
    fmt = body.get('format', 'markdown')
    if fmt not in ('markdown', 'json'):
        raise HTTPException(status_code=400, detail="FORMAT must be 'markdown' or 'json'")

    conn = get_db()
    try:
        svc = ExportService(conn)
        try:
            result = svc.export(output_id, fmt=fmt)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return result
    finally:
        conn.close()
```

- [ ] **Step 5: Register router in main.py**

Add:
```python
from api.export import router as export_router
app.include_router(export_router, prefix="/api/v1")
```

- [ ] **Step 6: Verify and commit**

```bash
cd /home/jjb/kb-platform/backend && python3 -c "from services.export_service import ExportService; print('OK')"
cd /home/jjb/kb-platform/backend && python3 -c "from api.export import router; print('OK')"
git add backend/services/export_service.py backend/api/export.py backend/main.py backend/tests/test_export_service.py
git commit -m "feat: add export service with markdown/JSON export and evidence index"
```

---

### Task 2: PSA Test Cases (PSA01-PSA08)

**Files:**
- Create: `backend/tests/test_psa_cases.py`

- [ ] **Step 1: Write PSA test cases**

```python
# backend/tests/test_psa_cases.py
import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_psa01_proposal_chapter_coverage():
    """PSA01: 方案生成每章证据覆盖率检查 — 无证据章节标待确认"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.proposal_service import ProposalService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = ProposalService(conn)
        result = svc.generate(project_id='p1', title='方案', evidences=[])
        for ch in result.get('risk_summary', []):
            assert '待补' in ch or '待确认' in ch
        assert len(result['risk_summary']) > 0
        conn.close()

def test_psa07_reply_strips_internal_notes():
    """PSA07: 客户答复存在内部备注 — 不输出给客户"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.reply_service import ReplyService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = ReplyService(conn)
        reply = svc.generate(
            customer_question='产品参数？',
            evidences=[{
                'id': 'ev-1',
                'claim': '支持4K',
                'body': '支持4K [内部备注:仅限特定型号]',
                'confidence': 0.9,
                'risk_flags': '[]',
            }],
        )
        assert '内部备注' not in reply['reply_text']
        assert '4K' in reply['reply_text']
        conn.close()

def test_psa08_export_with_evidence_index():
    """PSA08: 导出包含证据索引和版本号"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.output_service import OutputService
        from services.export_service import ExportService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = OutputService(conn)
        output = svc.create_output('proj-001', 'proposal', '公安方案',
            content_md='# 公安方案\n## 架构\n内容')
        exp = ExportService(conn, data_dir=tmpdir)
        result = exp.export(output['id'])
        assert result['version'] == 1
        with open(result['export_path'], 'r') as f:
            content = f.read()
        assert '证据索引' in content
        assert 'v1' in content
        conn.close()
```

- [ ] **Step 2: Verify tests pass**

```bash
cd /home/jjb/kb-platform/backend && python3 -c "
import sys; sys.path.insert(0, '.')
from tests.test_psa_cases import test_psa01_proposal_chapter_coverage, test_psa07_reply_strips_internal_notes, test_psa08_export_with_evidence_index
test_psa01_proposal_chapter_coverage(); print('PSA01 OK')
test_psa07_reply_strips_internal_notes(); print('PSA07 OK')
test_psa08_export_with_evidence_index(); print('PSA08 OK')
"
```

- [ ] **Step 3: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/tests/test_psa_cases.py
git commit -m "feat: add PSA test cases for proposal coverage, reply sanitization, export"
```
