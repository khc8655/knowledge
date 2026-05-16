# Pre-sales Workflows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the pre-sales workflow layer — Project CRUD, Proposal Generation, BOM/Configuration, Customer Reply, Template management, and Human Review APIs.

**Architecture:** Each workflow (proposal, BOM, reply) follows the same pattern: build Evidence Pack from search results → generate structured output using evidence constraints → persist output with evidence links → support human review. Templates provide reusable outlines. Projects provide context binding.

**Tech Stack:** Python 3, FastAPI, SQLite

---

## File Structure

**New files:**
- `backend/api/project.py` — Project CRUD: create, list, get, update, archive
- `backend/api/proposal.py` — Proposal generation: generate, regenerate-section, export
- `backend/api/bom.py` — BOM generation: generate with price/discontinued detection
- `backend/api/reply.py` — Customer reply: generate evidence-constrained reply
- `backend/api/template.py` — Template CRUD: create, list, get, update, delete
- `backend/api/output_review.py` — Human review: review actions, feedback
- `backend/services/proposal_service.py` — Proposal generation logic with evidence coverage
- `backend/services/bom_service.py` — BOM generation with price lookup and discontinued detection
- `backend/services/reply_service.py` — Reply generation with tone and evidence binding
- `backend/services/output_service.py` — Output management: create, update status, link evidence
- `backend/tests/test_project_api.py` — Project API tests
- `backend/tests/test_proposal_service.py` — Proposal service tests
- `backend/tests/test_bom_service.py` — BOM service tests
- `backend/tests/test_reply_service.py` — Reply service tests
- `backend/tests/test_template_api.py` — Template API tests
- `backend/tests/test_output_review.py` — Review API tests
- `backend/tests/test_presales_integration.py` — End-to-end workflow tests

**Modified files:**
- `backend/main.py` — Register all new routers

---

### Task 1: Project API

**Files:**
- Create: `backend/api/project.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_project_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_project_api.py
import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_create_and_get_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from api.project import create_project, get_project
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        proj = create_project({
            'customer_name': '测试客户',
            'industry': '公安',
            'deployment_type': '私有云',
            'description': '测试项目',
        }, conn=conn)
        assert proj['customer_name'] == '测试客户'
        assert proj['stage'] == 'draft'
        got = get_project(proj['id'], conn=conn)
        assert got['customer_name'] == '测试客户'
        conn.close()

def test_list_projects():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from api.project import create_project, list_projects
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        create_project({'customer_name': '客户A'}, conn=conn)
        create_project({'customer_name': '客户B'}, conn=conn)
        result = list_projects(conn=conn)
        assert result['total'] == 2
        conn.close()

def test_archive_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from api.project import create_project, archive_project
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        proj = create_project({'customer_name': '客户A'}, conn=conn)
        archive_project(proj['id'], conn=conn)
        rows = conn.execute("SELECT * FROM presales_projects WHERE id=? AND archived_at IS NOT NULL", (proj['id'],)).fetchall()
        assert len(rows) == 1
        conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_project_api.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# backend/api/project.py
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from db.models import get_db

router = APIRouter(prefix="/projects", tags=["projects"])


def create_project(data, conn=None):
    project_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO presales_projects (id, customer_name, industry, stage, deployment_type, description, owner, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (project_id, data.get('customer_name', ''),
         data.get('industry'), data.get('stage', 'draft'),
         data.get('deployment_type'), data.get('description'),
         data.get('owner'), now, now)
    )
    conn.commit()
    return get_project(project_id, conn=conn)


def get_project(project_id, conn=None):
    row = conn.execute("SELECT * FROM presales_projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        return None
    return dict(row)


def list_projects(page=1, page_size=20, stage=None, conn=None):
    conditions = ["archived_at IS NULL"]
    params = []
    if stage:
        conditions.append("stage = ?")
        params.append(stage)
    where = " WHERE " + " AND ".join(conditions)
    offset = (page - 1) * page_size
    total = conn.execute(f"SELECT COUNT(*) as c FROM presales_projects{where}", params).fetchone()['c']
    rows = conn.execute(
        f"SELECT * FROM presales_projects{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [page_size, offset]
    ).fetchall()
    return {"total": total, "page": page, "page_size": page_size, "items": [dict(r) for r in rows]}


def update_project(project_id, data, conn=None):
    now = datetime.now(timezone.utc).isoformat()
    fields = []
    params = []
    for key in ['customer_name', 'industry', 'stage', 'deployment_type', 'description', 'owner']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return get_project(project_id, conn=conn)
    fields.append("updated_at = ?")
    params.append(now)
    params.append(project_id)
    conn.execute(f"UPDATE presales_projects SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()
    return get_project(project_id, conn=conn)


def archive_project(project_id, conn=None):
    now = datetime.now(timezone.utc).isoformat()
    conn.execute("UPDATE presales_projects SET archived_at = ?, updated_at = ? WHERE id = ?", (now, now, project_id))
    conn.commit()


@router.post("")
async def api_create_project(body: dict):
    conn = get_db()
    try:
        if not body.get('customer_name'):
            raise HTTPException(status_code=400, detail="CUSTOMER_NAME_REQUIRED")
        return create_project(body, conn=conn)
    finally:
        conn.close()


@router.get("")
async def api_list_projects(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=200), stage: str = Query(None)):
    conn = get_db()
    try:
        return list_projects(page, page_size, stage, conn=conn)
    finally:
        conn.close()


@router.get("/{project_id}")
async def api_get_project(project_id: str):
    conn = get_db()
    try:
        proj = get_project(project_id, conn=conn)
        if not proj:
            raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")
        return proj
    finally:
        conn.close()


@router.put("/{project_id}")
async def api_update_project(project_id: str, body: dict):
    conn = get_db()
    try:
        if not get_project(project_id, conn=conn):
            raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")
        return update_project(project_id, body, conn=conn)
    finally:
        conn.close()


@router.post("/{project_id}/archive")
async def api_archive_project(project_id: str):
    conn = get_db()
    try:
        if not get_project(project_id, conn=conn):
            raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")
        archive_project(project_id, conn=conn)
        return {"status": "archived", "project_id": project_id}
    finally:
        conn.close()
```

- [ ] **Step 4: Register router in main.py**

```python
from api.project import router as project_router
app.include_router(project_router, prefix="/api/v1")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_project_api.py -v`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/api/project.py backend/main.py backend/tests/test_project_api.py && git commit -m "feat: add project CRUD API with create, list, get, update, archive"
```

---

### Task 2: Output Service (shared by all workflows)

**Files:**
- Create: `backend/services/output_service.py`
- Test: (tested via integration tests)

- [ ] **Step 1: Write implementation**

```python
# backend/services/output_service.py
import uuid
import json
from datetime import datetime, timezone


class OutputService:
    def __init__(self, conn):
        self.conn = conn

    def create_output(self, project_id, output_type, title, content_md=None, content_json=None):
        output_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """INSERT INTO project_outputs (id, project_id, output_type, title, status, content_md, content_json, version, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'draft', ?, ?, 1, ?, ?)""",
            (output_id, project_id, output_type, title,
             content_md, json.dumps(content_json or {}), now, now)
        )
        self.conn.commit()
        return self.get_output(output_id)

    def get_output(self, output_id):
        row = self.conn.execute("SELECT * FROM project_outputs WHERE id = ?", (output_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get('content_json'):
            try:
                d['content_json'] = json.loads(d['content_json'])
            except (json.JSONDecodeError, TypeError):
                d['content_json'] = {}
        return d

    def list_outputs(self, project_id, output_type=None):
        conditions = ["project_id = ?"]
        params = [project_id]
        if output_type:
            conditions.append("output_type = ?")
            params.append(output_type)
        where = " WHERE " + " AND ".join(conditions)
        rows = self.conn.execute(
            f"SELECT * FROM project_outputs{where} ORDER BY created_at DESC", params
        ).fetchall()
        return [dict(r) for r in rows]

    def update_output(self, output_id, content_md=None, content_json=None, title=None):
        now = datetime.now(timezone.utc).isoformat()
        fields = ["updated_at = ?"]
        params = [now]
        if content_md is not None:
            fields.append("content_md = ?")
            params.append(content_md)
        if content_json is not None:
            fields.append("content_json = ?")
            params.append(json.dumps(content_json))
        if title is not None:
            fields.append("title = ?")
            params.append(title)
        fields.append("version = version + 1")
        params.append(output_id)
        self.conn.execute(f"UPDATE project_outputs SET {', '.join(fields)} WHERE id = ?", params)
        self.conn.commit()
        return self.get_output(output_id)

    def update_status(self, output_id, status):
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE project_outputs SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, output_id)
        )
        self.conn.commit()

    def link_evidence(self, project_id, output_id, evidence_id, target_path, link_role='primary'):
        link_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """INSERT INTO project_evidence_links (id, project_id, output_id, evidence_id, target_path, link_role, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (link_id, project_id, output_id, evidence_id, target_path, link_role, now)
        )
        self.conn.commit()

    def get_evidence_links(self, output_id):
        rows = self.conn.execute(
            "SELECT * FROM project_evidence_links WHERE output_id = ?", (output_id,)
        ).fetchall()
        return [dict(r) for r in rows]
```

- [ ] **Step 2: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/services/output_service.py && git commit -m "feat: add output service for managing project outputs and evidence links"
```

---

### Task 3: Proposal Generation Service and API

**Files:**
- Create: `backend/services/proposal_service.py`
- Create: `backend/api/proposal.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_proposal_service.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_proposal_service.py
import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_generate_proposal_creates_output():
    """Proposal generation creates output with evidence coverage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.proposal_service import ProposalService
        from services.output_service import OutputService
        from evidence.pack import EvidencePackBuilder
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = ProposalService(conn)
        result = svc.generate(
            project_id='proj-001',
            title='测试方案',
            customer_context='公安行业客户',
            industry='公安',
            evidences=[],
        )
        assert result['output_id'] is not None
        assert result['status'] == 'draft'
        assert 'evidence_coverage' in result
        conn.close()

def test_proposal_low_coverage_flagged():
    """Chapters without evidence get flagged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.proposal_service import ProposalService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = ProposalService(conn)
        result = svc.generate(
            project_id='proj-001',
            title='测试方案',
            customer_context='客户背景',
            evidences=[],
        )
        assert any('待补证据' in r or '待确认' in r for r in result.get('risk_summary', []))
        conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_proposal_service.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# backend/services/proposal_service.py
from services.output_service import OutputService
from evidence.pack import EvidencePackBuilder

DEFAULT_CHAPTERS = [
    '项目背景与需求分析',
    '系统架构设计',
    '核心功能说明',
    '安全方案',
    '部署方案',
    '售后服务',
]


class ProposalService:
    def __init__(self, conn):
        self.conn = conn

    def generate(self, project_id, title, customer_context='', industry=None,
                 deployment_type=None, outline=None, template_id=None,
                 required_models=None, forbidden_models=None,
                 output_format='markdown', evidences=None):
        required_models = required_models or []
        forbidden_models = forbidden_models or []
        evidences = evidences or []

        # Determine chapters
        chapters = self._resolve_chapters(outline, template_id)
        content_json = {
            'chapters': [],
            'customer_context': customer_context,
            'industry': industry,
            'deployment_type': deployment_type,
        }

        # Assign evidence to chapters
        risk_summary = []
        for ch_title in chapters:
            matched = self._match_evidence_to_chapter(ch_title, evidences, required_models, forbidden_models)
            coverage = min(1.0, len(matched) * 0.5) if matched else 0.0
            chapter = {
                'title': ch_title,
                'evidence_ids': [e['evidence_id'] for e in matched],
                'coverage': coverage,
            }
            if coverage < 0.6:
                chapter['status'] = '待补证据'
                risk_summary.append(f"章节「{ch_title}」证据覆盖率不足 ({coverage:.0%})")
            else:
                chapter['status'] = 'evidence_ok'
            content_json['chapters'].append(chapter)

        # Generate preview markdown
        preview_md = self._generate_preview(title, content_json)

        # Create output
        output_svc = OutputService(self.conn)
        output = output_svc.create_output(
            project_id=project_id,
            output_type='proposal',
            title=title,
            content_md=preview_md,
            content_json=content_json,
        )

        # Link evidence
        for ch in content_json['chapters']:
            for eid in ch.get('evidence_ids', []):
                output_svc.link_evidence(project_id, output['id'], eid, ch['title'], 'primary')

        # Calculate overall evidence coverage
        coverage_map = {ch['title']: ch['coverage'] for ch in content_json['chapters']}

        return {
            'output_id': output['id'],
            'status': 'draft',
            'evidence_coverage': coverage_map,
            'risk_summary': risk_summary,
            'preview_md': preview_md,
        }

    def regenerate_section(self, output_id, chapter_title, evidences=None):
        output_svc = OutputService(self.conn)
        output = output_svc.get_output(output_id)
        if not output:
            return None
        content = output.get('content_json', {})
        for ch in content.get('chapters', []):
            if ch['title'] == chapter_title:
                matched = self._match_evidence_to_chapter(chapter_title, evidences or [], [], [])
                ch['evidence_ids'] = [e['evidence_id'] for e in matched]
                ch['coverage'] = min(1.0, len(matched) * 0.5) if matched else 0.0
                ch['status'] = 'evidence_ok' if ch['coverage'] >= 0.6 else '待补证据'
                break
        preview_md = self._generate_preview(output['title'], content)
        output_svc.update_output(output_id, content_md=preview_md, content_json=content)
        return output_svc.get_output(output_id)

    def _resolve_chapters(self, outline, template_id):
        if outline:
            return [line.strip() for line in outline.split('\n') if line.strip()]
        return DEFAULT_CHAPTERS

    def _match_evidence_to_chapter(self, chapter_title, evidences, required_models, forbidden_models):
        matched = []
        keywords = set()
        for kw in ['安全', '架构', '部署', '功能', '背景', '售后', '方案']:
            if kw in chapter_title:
                keywords.add(kw)
        for ev in evidences:
            ev_type = ev.get('evidence_type', '')
            claim = ev.get('claim', '')
            body = ev.get('body', '')
            score = 0
            for kw in keywords:
                if kw in claim or kw in body or kw in ev_type:
                    score += 1
            if required_models:
                for m in required_models:
                    if m in body or m in claim:
                        score += 1
            if forbidden_models:
                skip = False
                for m in forbidden_models:
                    if m in body:
                        skip = True
                        break
                if skip:
                    continue
            if score > 0:
                matched.append(ev)
        return matched[:5]

    def _generate_preview(self, title, content_json):
        lines = [f"# {title}\n"]
        for ch in content_json.get('chapters', []):
            status_marker = f" [{ch.get('status', '')}]" if ch.get('status') != 'evidence_ok' else ''
            lines.append(f"## {ch['title']}{status_marker}")
            if ch.get('evidence_ids'):
                lines.append(f"> 引用 {len(ch['evidence_ids'])} 条证据")
            lines.append('')
        return '\n'.join(lines)
```

- [ ] **Step 4: Create API**

```python
# backend/api/proposal.py
from fastapi import APIRouter, HTTPException
from db.models import get_db
from services.proposal_service import ProposalService
from evidence.pack import EvidencePackBuilder
from card.store import CardStore

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.post("/generate")
async def generate_proposal(body: dict):
    project_id = body.get('project_id')
    title = body.get('title')
    if not project_id or not title:
        raise HTTPException(status_code=400, detail="PROJECT_ID_AND_TITLE_REQUIRED")

    conn = get_db()
    try:
        # Build evidence from required models
        evidences = []
        required_models = body.get('required_models', [])
        if required_models:
            store = CardStore(conn)
            all_cards = store.list_cards(page_size=500).get('items', [])
            matching = [c for c in all_cards if any(m in c.get('body', '') for m in required_models)]
            builder = EvidencePackBuilder(conn)
            evidences = builder.build(matching, task_type='proposal', project_id=project_id)

        svc = ProposalService(conn)
        result = svc.generate(
            project_id=project_id,
            title=title,
            customer_context=body.get('customer_context', ''),
            industry=body.get('industry'),
            deployment_type=body.get('deployment_type'),
            outline=body.get('outline'),
            template_id=body.get('template_id'),
            required_models=required_models,
            forbidden_models=body.get('forbidden_models', []),
            output_format=body.get('output_format', 'markdown'),
            evidences=evidences,
        )
        return result
    finally:
        conn.close()


@router.post("/{output_id}/regenerate-section")
async def regenerate_section(output_id: str, body: dict):
    conn = get_db()
    try:
        svc = ProposalService(conn)
        result = svc.regenerate_section(output_id, body.get('chapter_title', ''), body.get('evidences'))
        if not result:
            raise HTTPException(status_code=404, detail="OUTPUT_NOT_FOUND")
        return result
    finally:
        conn.close()
```

- [ ] **Step 5: Register router**

```python
from api.proposal import router as proposal_router
app.include_router(proposal_router, prefix="/api/v1")
```

- [ ] **Step 6: Run test and commit**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_proposal_service.py -v`

```bash
cd /home/jjb/kb-platform && git add backend/services/proposal_service.py backend/api/proposal.py backend/main.py backend/tests/test_proposal_service.py && git commit -m "feat: add proposal generation service and API with evidence coverage"
```

---

### Task 4: BOM Service and API

**Files:**
- Create: `backend/services/bom_service.py`
- Create: `backend/api/bom.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_bom_service.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_bom_service.py
import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_bom_generate_from_evidence():
    """BOM generation extracts price lines from evidence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.bom_service import BomService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = BomService(conn)
        evidences = [
            {
                'evidence_id': 'ev-001',
                'source_card_id': '01-01-test-sec-001',
                'evidence_type': 'price',
                'claim': 'AE800 报价',
                'body': 'AE800套装 价格:138000',
                'source': '报价.xlsx:Sheet1:5',
                'confidence': 0.95,
                'freshness': 'current',
                'risk_flags': [],
            },
            {
                'evidence_id': 'ev-002',
                'source_card_id': '01-01-test-sec-002',
                'evidence_type': 'price',
                'claim': 'TP10 配件价格',
                'body': 'TP10摄像头 价格:3800',
                'source': '报价.xlsx:Sheet2:10',
                'confidence': 0.95,
                'freshness': 'current',
                'risk_flags': [],
            },
        ]
        result = svc.generate(
            project_id='proj-001',
            scenario='视频会议',
            evidences=evidences,
        )
        assert result['output_id'] is not None
        assert len(result['lines']) >= 1
        conn.close()

def test_bom_detects_discontinued():
    """BOM detects discontinued products and flags risk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.bom_service import BomService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = BomService(conn)
        evidences = [
            {
                'evidence_id': 'ev-003',
                'source_card_id': '01-01-test-sec-003',
                'evidence_type': 'price',
                'claim': 'PE8000 报价',
                'body': 'PE8000 价格:252000 停产',
                'source': '报价.xlsx:Sheet1:10',
                'confidence': 0.95,
                'freshness': 'current',
                'risk_flags': [],
            },
        ]
        result = svc.generate(project_id='proj-001', scenario='测试', evidences=evidences)
        assert any('停产' in r or 'discontinued' in r.lower() for r in result.get('risk_summary', []))
        conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_bom_service.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# backend/services/bom_service.py
import re
from services.output_service import OutputService

PRICE_PATTERN = re.compile(r'价格[：:]\s*(\d+(?:\.\d+)?)')
DISCONTINUED_KEYWORDS = ['停产', '停售', '替代', 'EOL', '停']


class BomService:
    def __init__(self, conn):
        self.conn = conn

    def generate(self, project_id, scenario, room_count=None, deployment_type=None,
                 required_models=None, budget_limit=None, evidences=None):
        evidences = evidences or []
        required_models = required_models or []

        lines = []
        risk_summary = []

        for ev in evidences:
            body = ev.get('body', '')
            source = ev.get('source', '')
            ev_type = ev.get('evidence_type', '')

            # Extract product info
            model = self._extract_model(body)
            price = self._extract_price(body)
            name = ev.get('claim', model or '未知产品')

            # Check discontinued
            is_discontinued = any(kw in body for kw in DISCONTINUED_KEYWORDS)
            risk_flags = []
            if is_discontinued:
                risk_flags.append('discontinued')
                risk_summary.append(f"产品 {name} 已停产，建议查找替代型号")

            # Check missing price
            if price is None and ev_type == 'price':
                risk_flags.append('missing_price')
                risk_summary.append(f"产品 {name} 未找到价格信息")

            line = {
                'name': name,
                'model': model,
                'quantity': room_count or 1,
                'unit_price': price,
                'total_price': price * (room_count or 1) if price else None,
                'source': source,
                'risk_flags': risk_flags,
            }
            lines.append(line)

        # Check required models not in evidence
        found_models = {l['model'] for l in lines if l.get('model')}
        for m in required_models:
            if m not in found_models:
                risk_summary.append(f"所需型号 {m} 未在证据中找到")

        # Budget check
        total = sum(l.get('total_price') or 0 for l in lines)
        if budget_limit and total > budget_limit:
            risk_summary.append(f"总价 {total} 超出预算 {budget_limit}")

        # Create output
        output_svc = OutputService(self.conn)
        content_json = {
            'scenario': scenario,
            'room_count': room_count,
            'deployment_type': deployment_type,
            'lines': lines,
            'total_price': total or None,
        }
        output = output_svc.create_output(
            project_id=project_id,
            output_type='bom',
            title=f'BOM-{scenario}',
            content_json=content_json,
        )

        return {
            'output_id': output['id'],
            'lines': lines,
            'total_price': total or None,
            'risk_summary': risk_summary,
        }

    def _extract_price(self, body):
        match = PRICE_PATTERN.search(body)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    def _extract_model(self, body):
        match = re.search(r'[A-Z]{2,}\d{3,}', body)
        return match.group(0) if match else None
```

- [ ] **Step 4: Create API**

```python
# backend/api/bom.py
from fastapi import APIRouter, HTTPException
from db.models import get_db
from services.bom_service import BomService
from evidence.pack import EvidencePackBuilder
from card.store import CardStore

router = APIRouter(prefix="/bom", tags=["bom"])


@router.post("/generate")
async def generate_bom(body: dict):
    project_id = body.get('project_id')
    scenario = body.get('scenario')
    if not project_id or not scenario:
        raise HTTPException(status_code=400, detail="PROJECT_ID_AND_SCENARIO_REQUIRED")

    conn = get_db()
    try:
        # Build evidence from required models
        evidences = []
        required_models = body.get('required_models', [])
        if required_models:
            store = CardStore(conn)
            all_cards = store.list_cards(page_size=500).get('items', [])
            matching = [c for c in all_cards if any(m in c.get('body', '') for m in required_models)]
            builder = EvidencePackBuilder(conn)
            evidences = builder.build(matching, task_type='bom', project_id=project_id)

        svc = BomService(conn)
        return svc.generate(
            project_id=project_id,
            scenario=scenario,
            room_count=body.get('room_count'),
            deployment_type=body.get('deployment_type'),
            required_models=required_models,
            budget_limit=body.get('budget_limit'),
            evidences=evidences,
        )
    finally:
        conn.close()
```

- [ ] **Step 5: Register router and commit**

```python
from api.bom import router as bom_router
app.include_router(bom_router, prefix="/api/v1")
```

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_bom_service.py -v`

```bash
cd /home/jjb/kb-platform && git add backend/services/bom_service.py backend/api/bom.py backend/main.py backend/tests/test_bom_service.py && git commit -m "feat: add BOM generation service and API with price extraction and discontinued detection"
```

---

### Task 5: Customer Reply Service and API

**Files:**
- Create: `backend/services/reply_service.py`
- Create: `backend/api/reply.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_reply_service.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_reply_service.py
import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_reply_generate_with_evidence():
    """Reply generation uses evidence to build response."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.reply_service import ReplyService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = ReplyService(conn)
        evidences = [
            {
                'evidence_id': 'ev-001',
                'evidence_type': 'price',
                'claim': 'AE800 报价',
                'body': 'AE800套装 价格:138000',
                'source': '报价.xlsx:Sheet1:5',
                'confidence': 0.95,
                'risk_flags': [],
            }
        ]
        result = svc.generate(
            customer_question='AE800多少钱？',
            evidences=evidences,
        )
        assert result['output_id'] is not None
        assert len(result['reply_text']) > 0
        assert '138000' in result['reply_text'] or 'AE800' in result['reply_text']
        conn.close()

def test_reply_no_evidence_returns_uncertain():
    """Without evidence, reply indicates uncertainty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.reply_service import ReplyService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = ReplyService(conn)
        result = svc.generate(
            customer_question='XYZ产品的价格？',
            evidences=[],
        )
        assert '待确认' in result['reply_text'] or '暂无' in result['reply_text']
        conn.close()

def test_reply_filters_internal_notes():
    """Internal notes not included in customer-facing reply."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.reply_service import ReplyService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = ReplyService(conn)
        evidences = [
            {
                'evidence_id': 'ev-001',
                'evidence_type': 'parameter',
                'claim': '功能说明',
                'body': '支持4K [内部备注: 成本较高]',
                'source': '白皮书.docx',
                'confidence': 0.8,
                'risk_flags': [],
            }
        ]
        result = svc.generate(
            customer_question='支持4K吗？',
            evidences=evidences,
        )
        assert '内部备注' not in result['reply_text']
        conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_reply_service.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# backend/services/reply_service.py
import re
from services.output_service import OutputService

INTERNAL_PATTERNS = [
    r'\[内部备注[：:][^\]]*\]',
    r'\[内部[：:][^\]]*\]',
    r'\[confidential[：:][^\]]*\]',
]


class ReplyService:
    def __init__(self, conn):
        self.conn = conn

    def generate(self, customer_question, evidences=None, project_id=None,
                 tone='concise', max_chars=800, allowed_evidence_ids=None):
        evidences = evidences or []
        if allowed_evidence_ids:
            evidences = [e for e in evidences if e.get('evidence_id') in allowed_evidence_ids]

        risk_summary = []
        reply_parts = []

        if not evidences:
            reply_parts.append(f"关于「{customer_question}」，暂无相关证据支持，建议待确认后回复。")
            risk_summary.append("无证据支持，答复内容需人工确认")
        else:
            # Build reply from evidence
            reply_parts.append(f"关于「{customer_question}」：\n")
            for ev in evidences:
                body = self._sanitize(ev.get('body', ''))
                source = ev.get('source', '')
                ev_type = ev.get('evidence_type', '')

                if ev.get('risk_flags'):
                    for flag in ev['risk_flags']:
                        if flag == 'expired_certificate':
                            risk_summary.append("引用了过期证书，请注意时效性")
                        elif flag == 'discontinued':
                            risk_summary.append("涉及已停产产品")

                reply_parts.append(f"- {body}")
                if source:
                    reply_parts.append(f"  （出处：{source}）")

            # Add disclaimer if confidence is low
            avg_conf = sum(e.get('confidence', 0) for e in evidences) / len(evidences)
            if avg_conf < 0.7:
                risk_summary.append("证据置信度较低，建议人工审核")
                reply_parts.append("\n以上信息仅供参考，具体以实际确认为准。")

        reply_text = '\n'.join(reply_parts)
        if len(reply_text) > max_chars:
            reply_text = reply_text[:max_chars - 3] + '...'

        # Create output
        output_svc = OutputService(self.conn)
        output = output_svc.create_output(
            project_id=project_id or 'standalone',
            output_type='reply',
            title=f'客户答复-{customer_question[:30]}',
            content_md=reply_text,
            content_json={
                'customer_question': customer_question,
                'tone': tone,
                'evidence_count': len(evidences),
            },
        )

        # Link evidence
        for ev in evidences:
            output_svc.link_evidence(
                project_id or 'standalone', output['id'],
                ev.get('evidence_id', ''), 'reply', 'primary'
            )

        return {
            'output_id': output['id'],
            'reply_text': reply_text,
            'internal_evidence': evidences,
            'risk_summary': risk_summary,
        }

    def _sanitize(self, text):
        for pattern in INTERNAL_PATTERNS:
            text = re.sub(pattern, '', text)
        return text.strip()
```

- [ ] **Step 4: Create API**

```python
# backend/api/reply.py
from fastapi import APIRouter, HTTPException
from db.models import get_db
from services.reply_service import ReplyService
from evidence.pack import EvidencePackBuilder
from card.store import CardStore

router = APIRouter(prefix="/reply", tags=["reply"])


@router.post("/generate")
async def generate_reply(body: dict):
    customer_question = body.get('customer_question', '')
    if not customer_question:
        raise HTTPException(status_code=400, detail="CUSTOMER_QUESTION_REQUIRED")

    conn = get_db()
    try:
        # Search for relevant evidence
        store = CardStore(conn)
        all_cards = store.list_cards(page_size=200).get('items', [])
        # Simple keyword matching
        keywords = customer_question.split()
        matching = []
        for card in all_cards:
            score = sum(1 for kw in keywords if kw in card.get('body', '') or kw in card.get('title', ''))
            if score > 0:
                matching.append(card)

        builder = EvidencePackBuilder(conn)
        evidences = builder.build(matching[:5], task_type='reply',
                                   project_id=body.get('project_id'))

        svc = ReplyService(conn)
        return svc.generate(
            customer_question=customer_question,
            evidences=evidences,
            project_id=body.get('project_id'),
            tone=body.get('tone', 'concise'),
            max_chars=body.get('max_chars', 800),
            allowed_evidence_ids=body.get('allowed_evidence_ids'),
        )
    finally:
        conn.close()
```

- [ ] **Step 5: Register router and commit**

```python
from api.reply import router as reply_router
app.include_router(reply_router, prefix="/api/v1")
```

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_reply_service.py -v`

```bash
cd /home/jjb/kb-platform && git add backend/services/reply_service.py backend/api/reply.py backend/main.py backend/tests/test_reply_service.py && git commit -m "feat: add customer reply service and API with evidence sanitization"
```

---

### Task 6: Template API

**Files:**
- Create: `backend/api/template.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_template_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_template_api.py
import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_template_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from api.template import create_template, get_template, list_templates, update_template, delete_template
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        t = create_template({
            'template_type': 'proposal',
            'name': '公安方案模板',
            'industry': '公安',
            'file_path': 'templates/proposal/police.md',
        }, conn=conn)
        assert t['name'] == '公安方案模板'
        assert t['enabled'] == 1
        got = get_template(t['id'], conn=conn)
        assert got is not None
        items = list_templates(template_type='proposal', conn=conn)
        assert items['total'] == 1
        update_template(t['id'], {'name': '更新后模板'}, conn=conn)
        got2 = get_template(t['id'], conn=conn)
        assert got2['name'] == '更新后模板'
        delete_template(t['id'], conn=conn)
        assert get_template(t['id'], conn=conn) is None
        conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_template_api.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# backend/api/template.py
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from db.models import get_db

router = APIRouter(prefix="/templates", tags=["templates"])


def create_template(data, conn=None):
    template_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO templates (id, template_type, name, industry, deployment_type, file_path, schema_json, enabled, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (template_id, data.get('template_type'), data.get('name', ''),
         data.get('industry'), data.get('deployment_type'),
         data.get('file_path', ''), data.get('schema_json', '{}'),
         data.get('enabled', 1), now, now)
    )
    conn.commit()
    return get_template(template_id, conn=conn)


def get_template(template_id, conn=None):
    row = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,)).fetchone()
    return dict(row) if row else None


def list_templates(template_type=None, industry=None, conn=None):
    conditions = ["enabled = 1"]
    params = []
    if template_type:
        conditions.append("template_type = ?")
        params.append(template_type)
    if industry:
        conditions.append("industry = ?")
        params.append(industry)
    where = " WHERE " + " AND ".join(conditions)
    rows = conn.execute(f"SELECT * FROM templates{where} ORDER BY created_at DESC", params).fetchall()
    return {"total": len(rows), "items": [dict(r) for r in rows]}


def update_template(template_id, data, conn=None):
    now = datetime.now(timezone.utc).isoformat()
    fields = []
    params = []
    for key in ['name', 'industry', 'deployment_type', 'file_path', 'schema_json', 'enabled']:
        if key in data:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return get_template(template_id, conn=conn)
    fields.append("updated_at = ?")
    params.append(now)
    params.append(template_id)
    conn.execute(f"UPDATE templates SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()
    return get_template(template_id, conn=conn)


def delete_template(template_id, conn=None):
    conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    conn.commit()


@router.post("")
async def api_create_template(body: dict):
    conn = get_db()
    try:
        if not body.get('template_type'):
            raise HTTPException(status_code=400, detail="TEMPLATE_TYPE_REQUIRED")
        return create_template(body, conn=conn)
    finally:
        conn.close()


@router.get("")
async def api_list_templates(template_type: str = Query(None), industry: str = Query(None)):
    conn = get_db()
    try:
        return list_templates(template_type, industry, conn=conn)
    finally:
        conn.close()


@router.get("/{template_id}")
async def api_get_template(template_id: str):
    conn = get_db()
    try:
        t = get_template(template_id, conn=conn)
        if not t:
            raise HTTPException(status_code=404, detail="TEMPLATE_NOT_FOUND")
        return t
    finally:
        conn.close()


@router.put("/{template_id}")
async def api_update_template(template_id: str, body: dict):
    conn = get_db()
    try:
        if not get_template(template_id, conn=conn):
            raise HTTPException(status_code=404, detail="TEMPLATE_NOT_FOUND")
        return update_template(template_id, body, conn=conn)
    finally:
        conn.close()


@router.delete("/{template_id}")
async def api_delete_template(template_id: str):
    conn = get_db()
    try:
        if not get_template(template_id, conn=conn):
            raise HTTPException(status_code=404, detail="TEMPLATE_NOT_FOUND")
        delete_template(template_id, conn=conn)
        return {"status": "deleted", "template_id": template_id}
    finally:
        conn.close()
```

- [ ] **Step 4: Register router and commit**

```python
from api.template import router as template_router
app.include_router(template_router, prefix="/api/v1")
```

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_template_api.py -v`

```bash
cd /home/jjb/kb-platform && git add backend/api/template.py backend/main.py backend/tests/test_template_api.py && git commit -m "feat: add template CRUD API for proposal/tender/reply/ppt templates"
```

---

### Task 7: Output Review API

**Files:**
- Create: `backend/api/output_review.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_output_review.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_output_review.py
import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_review_status_transitions():
    """Review actions change output status correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.output_service import OutputService
        from api.output_review import review_output, submit_feedback
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = OutputService(conn)
        output = svc.create_output('proj-001', 'proposal', '测试方案')
        assert output['status'] == 'draft'
        review_output(output['id'], {'action': 'mark_evidence_checked'}, conn=conn)
        o = svc.get_output(output['id'])
        assert o['status'] == 'evidence_checked'
        review_output(output['id'], {'action': 'mark_human_reviewed', 'reviewer': '张三'}, conn=conn)
        o = svc.get_output(output['id'])
        assert o['status'] == 'human_reviewed'
        conn.close()

def test_submit_feedback():
    """Feedback is recorded correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.output_service import OutputService
        from api.output_review import submit_feedback
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = OutputService(conn)
        output = svc.create_output('proj-001', 'proposal', '测试方案')
        submit_feedback(output['id'], {
            'feedback_type': 'edit',
            'target_path': '第一章',
            'before_text': '旧内容',
            'after_text': '新内容',
        }, conn=conn)
        rows = conn.execute("SELECT * FROM project_feedback WHERE output_id=?", (output['id'],)).fetchall()
        assert len(rows) == 1
        assert rows[0]['feedback_type'] == 'edit'
        conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_output_review.py -v`
Expected: FAIL

- [ ] **Step 3: Write implementation**

```python
# backend/api/output_review.py
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from db.models import get_db
from services.output_service import OutputService

router = APIRouter(prefix="/outputs", tags=["outputs"])

VALID_TRANSITIONS = {
    'draft': ['evidence_checked'],
    'evidence_checked': ['human_reviewed'],
    'human_reviewed': ['exported'],
    'exported': ['archived'],
}


@router.post("/{output_id}/review")
async def review_output(output_id: str, body: dict):
    action = body.get('action')
    if not action:
        raise HTTPException(status_code=400, detail="ACTION_REQUIRED")

    conn = get_db()
    try:
        svc = OutputService(conn)
        output = svc.get_output(output_id)
        if not output:
            raise HTTPException(status_code=404, detail="OUTPUT_NOT_FOUND")

        target_status = action.replace('mark_', '')
        current = output['status']
        allowed = VALID_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise HTTPException(status_code=409, detail=f"INVALID_TRANSITION: {current} → {target_status}")

        svc.update_status(output_id, target_status)

        if body.get('reviewer'):
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "UPDATE project_outputs SET reviewed_by=?, reviewed_at=? WHERE id=?",
                (body['reviewer'], now, output_id)
            )
            conn.commit()

        return {"status": target_status, "output_id": output_id}
    finally:
        conn.close()


@router.post("/{output_id}/feedback")
async def submit_feedback(output_id: str, body: dict):
    feedback_type = body.get('feedback_type')
    if not feedback_type:
        raise HTTPException(status_code=400, detail="FEEDBACK_TYPE_REQUIRED")

    conn = get_db()
    try:
        svc = OutputService(conn)
        output = svc.get_output(output_id)
        if not output:
            raise HTTPException(status_code=404, detail="OUTPUT_NOT_FOUND")

        feedback_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO project_feedback (id, project_id, output_id, feedback_type, target_path, before_text, after_text, comment, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (feedback_id, output['project_id'], output_id, feedback_type,
             body.get('target_path'), body.get('before_text'),
             body.get('after_text'), body.get('comment'),
             body.get('created_by'), now)
        )
        conn.commit()
        return {"status": "recorded", "feedback_id": feedback_id}
    finally:
        conn.close()


def review_output(output_id, body, conn=None):
    """Helper for tests."""
    svc = OutputService(conn)
    output = svc.get_output(output_id)
    if not output:
        return None
    target_status = body.get('action', '').replace('mark_', '')
    svc.update_status(output_id, target_status)
    if body.get('reviewer'):
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE project_outputs SET reviewed_by=?, reviewed_at=? WHERE id=?",
            (body['reviewer'], now, output_id)
        )
        conn.commit()
    return svc.get_output(output_id)


def submit_feedback(output_id, body, conn=None):
    """Helper for tests."""
    svc = OutputService(conn)
    output = svc.get_output(output_id)
    if not output:
        return None
    feedback_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO project_feedback (id, project_id, output_id, feedback_type, target_path, before_text, after_text, comment, created_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (feedback_id, output['project_id'], output_id, body.get('feedback_type'),
         body.get('target_path'), body.get('before_text'),
         body.get('after_text'), body.get('comment'),
         body.get('created_by'), now)
    )
    conn.commit()
    return {"status": "recorded", "feedback_id": feedback_id}
```

- [ ] **Step 4: Register router and commit**

```python
from api.output_review import router as review_router
app.include_router(review_router, prefix="/api/v1")
```

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_output_review.py -v`

```bash
cd /home/jjb/kb-platform && git add backend/api/output_review.py backend/main.py backend/tests/test_output_review.py && git commit -m "feat: add output review API with status transitions and feedback"
```

---

### Task 8: Pre-sales Integration Test

**Files:**
- Create: `backend/tests/test_presales_integration.py`

- [ ] **Step 1: Write integration test**

```python
# backend/tests/test_presales_integration.py
import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_full_presales_workflow():
    """End-to-end: create project → generate proposal → review → generate BOM → reply."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from api.project import create_project
        from services.proposal_service import ProposalService
        from services.bom_service import BomService
        from services.reply_service import ReplyService
        from services.output_service import OutputService
        from api.output_review import review_output

        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)

        # 1. Create project
        proj = create_project({'customer_name': '测试客户', 'industry': '公安'}, conn=conn)
        assert proj['id'] is not None

        # 2. Generate proposal
        proposal_svc = ProposalService(conn)
        proposal = proposal_svc.generate(
            project_id=proj['id'],
            title='公安视频方案',
            customer_context='公安行业',
            evidences=[],
        )
        assert proposal['output_id'] is not None
        assert len(proposal['risk_summary']) > 0  # No evidence = risk

        # 3. Review proposal
        review_output(proposal['output_id'], {'action': 'mark_evidence_checked'}, conn=conn)
        output_svc = OutputService(conn)
        o = output_svc.get_output(proposal['output_id'])
        assert o['status'] == 'evidence_checked'

        # 4. Generate BOM
        bom_svc = BomService(conn)
        bom = bom_svc.generate(
            project_id=proj['id'],
            scenario='视频会议',
            evidences=[{
                'evidence_id': 'ev-001',
                'evidence_type': 'price',
                'claim': 'AE800',
                'body': 'AE800 价格:138000',
                'source': '报价.xlsx:Sheet1:5',
                'confidence': 0.95,
                'risk_flags': [],
            }],
        )
        assert bom['output_id'] is not None
        assert len(bom['lines']) >= 1

        # 5. Generate reply
        reply_svc = ReplyService(conn)
        reply = reply_svc.generate(
            customer_question='AE800支持4K吗？',
            evidences=[{
                'evidence_id': 'ev-002',
                'evidence_type': 'parameter',
                'claim': '4K支持',
                'body': 'AE800支持4K超高清',
                'source': '白皮书.docx',
                'confidence': 0.9,
                'risk_flags': [],
            }],
            project_id=proj['id'],
        )
        assert reply['output_id'] is not None
        assert '4K' in reply['reply_text']

        # 6. Verify all outputs linked to project
        outputs = output_svc.list_outputs(proj['id'])
        assert len(outputs) == 3  # proposal + bom + reply

        conn.close()
```

- [ ] **Step 2: Run test**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_presales_integration.py -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/tests/test_presales_integration.py && git commit -m "feat: add pre-sales workflow integration test"
```
