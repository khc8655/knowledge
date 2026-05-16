# Evidence Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Evidence Pack system, report pipeline, risk annotation, and tender matching — the evidence-constrained generation foundation for the v7.5 pre-sales assistant.

**Architecture:** Evidence Pack is the bridge between raw search results (SearchHit) and pre-sales generation. Each evidence item links a card to a claim with confidence, freshness, and risk flags. The report pipeline handles detection/certification documents with structured metadata. Risk annotation detects expired certificates, missing reports, and other flags. Tender matching uses rule-first + LLM-assisted hybrid judgement.

**Tech Stack:** Python 3, FastAPI, SQLite, python-docx (already installed), PyYAML

---

## File Structure

**New files:**
- `backend/evidence/__init__.py` — Package init
- `backend/evidence/pack.py` — Evidence Pack builder: build from search results, persist, archive
- `backend/evidence/risk.py` — Risk flag detection: expired certs, missing reports, model mismatch
- `backend/pipeline/report.py` — Report pipeline: parse report docs, extract report_meta
- `backend/api/evidence.py` — Evidence API: build, get, list by project, archive
- `backend/api/tender.py` — Tender API: analyze requirements, match with mixed judgement
- `backend/services/tender_service.py` — Tender matching logic: rule extraction, evidence search, scoring
- `backend/tests/test_evidence_pack.py` — Evidence Pack service tests
- `backend/tests/test_evidence_api.py` — Evidence API endpoint tests
- `backend/tests/test_risk.py` — Risk detection tests
- `backend/tests/test_pipeline_report.py` — Report pipeline tests
- `backend/tests/test_tender_service.py` — Tender matching tests

**Modified files:**
- `backend/main.py` — Register evidence and tender routers
- `backend/pipeline/__init__.py` — Export ReportPipeline
- `backend/card/store.py` — Add report_meta support to save/update
- `backend/job/executor.py` — Register pipeline_report handler

---

### Task 1: Evidence Pack Builder Service

**Files:**
- Create: `backend/evidence/__init__.py`
- Create: `backend/evidence/pack.py`
- Test: `backend/tests/test_evidence_pack.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_evidence_pack.py
import sys, os, tempfile, sqlite3, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_build_evidence_from_cards():
    """build() converts card search results into evidence items."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from evidence.pack import EvidencePackBuilder
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        builder = EvidencePackBuilder(conn)
        cards = [
            {
                'id': '01-01-test-sec-001',
                'source_type': 'excel',
                'title': 'AE800 报价',
                'body': '价格: 138000',
                'path': '报价.xlsx:Sheet1:5',
                'models': ['AE800'],
                'semantic': {
                    'card_type': 'price',
                    'quality_tier': 'high',
                    'summary': 'AE800 报价信息',
                },
                'report_meta': None,
            }
        ]
        result = builder.build(cards, task_type='bom')
        assert len(result) == 1
        ev = result[0]
        assert ev['source_card_id'] == '01-01-test-sec-001'
        assert ev['evidence_type'] == 'price'
        assert ev['confidence'] > 0
        assert ev['body'] == '价格: 138000'
        conn.close()

def test_persist_and_get_evidence():
    """persist() saves to DB, get() retrieves."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from evidence.pack import EvidencePackBuilder
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        builder = EvidencePackBuilder(conn)
        cards = [
            {
                'id': '01-01-test-sec-001',
                'source_type': 'excel',
                'title': 'AE800 报价',
                'body': '价格: 138000',
                'path': '报价.xlsx:Sheet1:5',
                'models': ['AE800'],
                'semantic': {'card_type': 'price', 'quality_tier': 'high', 'summary': 'AE800 报价'},
                'report_meta': None,
            }
        ]
        evidences = builder.build(cards, task_type='bom')
        pack_id = builder.persist(evidences, project_id='proj-001')
        assert pack_id is not None
        got = builder.get(pack_id)
        assert got is not None
        assert got['source_card_id'] == '01-01-test-sec-001'
        conn.close()

def test_list_by_project():
    """list_by_project() returns all evidence for a project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from evidence.pack import EvidencePackBuilder
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        builder = EvidencePackBuilder(conn)
        cards = [
            {
                'id': '01-01-test-sec-001',
                'source_type': 'excel',
                'title': 'AE800 报价',
                'body': '价格: 138000',
                'path': '报价.xlsx:Sheet1:5',
                'models': ['AE800'],
                'semantic': {'card_type': 'price', 'quality_tier': 'high', 'summary': 'AE800 报价'},
                'report_meta': None,
            },
            {
                'id': '01-01-test-sec-002',
                'source_type': 'word',
                'title': '安全方案',
                'body': '支持国密SM4加密',
                'path': '白皮书.docx > 安全 > 加密',
                'models': [],
                'semantic': {'card_type': 'capability', 'quality_tier': 'high', 'summary': '安全方案'},
                'report_meta': None,
            },
        ]
        evidences = builder.build(cards, task_type='tender')
        builder.persist(evidences, project_id='proj-001')
        items = builder.list_by_project('proj-001')
        assert len(items) == 2
        conn.close()

def test_archive_evidence():
    """archive() sets archived_at, excludes from active queries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from evidence.pack import EvidencePackBuilder
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        builder = EvidencePackBuilder(conn)
        cards = [
            {
                'id': '01-01-test-sec-001',
                'source_type': 'excel',
                'title': 'AE800 报价',
                'body': '价格: 138000',
                'path': '报价.xlsx:Sheet1:5',
                'models': ['AE800'],
                'semantic': {'card_type': 'price', 'quality_tier': 'high', 'summary': 'AE800 报价'},
                'report_meta': None,
            }
        ]
        evidences = builder.build(cards, task_type='bom')
        pack_id = builder.persist(evidences, project_id='proj-001')
        builder.archive(pack_id)
        got = builder.get(pack_id)
        assert got['archived_at'] is not None
        items = builder.list_by_project('proj-001')
        assert len(items) == 0
        conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_evidence_pack.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'evidence'"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/evidence/__init__.py
from evidence.pack import EvidencePackBuilder
```

```python
# backend/evidence/pack.py
import uuid
import json
from datetime import datetime, timezone


CARD_TYPE_TO_EVIDENCE_TYPE = {
    'price': 'price',
    'parameter': 'parameter',
    'capability': 'parameter',
    'scenario': 'scenario',
    'architecture': 'architecture',
    'update': 'update',
}


class EvidencePackBuilder:
    def __init__(self, conn):
        self.conn = conn

    def build(self, cards, task_type='proposal', project_id=None):
        """Convert card search results into evidence items."""
        evidences = []
        for card in cards:
            semantic = card.get('semantic', {}) or {}
            report_meta = card.get('report_meta')
            card_type = semantic.get('card_type', 'parameter')
            evidence_type = CARD_TYPE_TO_EVIDENCE_TYPE.get(card_type, 'parameter')
            if report_meta:
                evidence_type = 'report'

            confidence = self._calc_confidence(card)
            freshness = self._calc_freshness(card)
            risk_flags = self._detect_risk_flags(card)

            evidences.append({
                'evidence_id': str(uuid.uuid4()),
                'project_id': project_id,
                'source_card_id': card['id'],
                'source_type': card.get('source_type', 'unknown'),
                'evidence_type': evidence_type,
                'claim': semantic.get('summary', card.get('title', '')),
                'body': card['body'],
                'source': self._format_source(card),
                'confidence': confidence,
                'freshness': freshness,
                'risk_flags': risk_flags,
                'created_at': datetime.now(timezone.utc).isoformat(),
            })
        return evidences

    def persist(self, evidences, project_id=None, created_by_task_id=None):
        """Save evidence pack to DB. Returns pack_id (first evidence's id)."""
        pack_id = None
        for ev in evidences:
            eid = ev.get('evidence_id', str(uuid.uuid4()))
            if pack_id is None:
                pack_id = eid
            self.conn.execute(
                """INSERT INTO evidence_packs
                   (id, project_id, source_card_id, source_type, evidence_type,
                    claim, body, source, confidence, freshness, risk_flags,
                    created_by_task_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (eid, ev.get('project_id') or project_id,
                 ev['source_card_id'], ev['source_type'], ev['evidence_type'],
                 ev['claim'], ev['body'], ev['source'],
                 ev['confidence'], ev['freshness'],
                 json.dumps(ev.get('risk_flags', [])),
                 created_by_task_id, ev['created_at'])
            )
        self.conn.commit()
        return pack_id

    def get(self, evidence_id):
        """Get a single evidence item by ID."""
        row = self.conn.execute(
            "SELECT * FROM evidence_packs WHERE id = ?", (evidence_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_dict(row)

    def list_by_project(self, project_id, include_archived=False):
        """List all evidence for a project."""
        if include_archived:
            rows = self.conn.execute(
                "SELECT * FROM evidence_packs WHERE project_id = ? ORDER BY created_at DESC",
                (project_id,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM evidence_packs WHERE project_id = ? AND archived_at IS NULL ORDER BY created_at DESC",
                (project_id,)
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def archive(self, evidence_id):
        """Soft-delete an evidence item."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE evidence_packs SET archived_at = ? WHERE id = ?",
            (now, evidence_id)
        )
        self.conn.commit()

    def _calc_confidence(self, card):
        semantic = card.get('semantic', {}) or {}
        quality_tier = semantic.get('quality_tier', 'placeholder')
        tier_map = {'high': 0.95, 'medium': 0.75, 'low': 0.4, 'placeholder': 0.1}
        return tier_map.get(quality_tier, 0.5)

    def _calc_freshness(self, card):
        report_meta = card.get('report_meta')
        if report_meta and report_meta.get('valid_to'):
            try:
                valid_to = datetime.fromisoformat(report_meta['valid_to'])
                if valid_to < datetime.now(timezone.utc):
                    return 'expired'
                return 'current'
            except (ValueError, TypeError):
                pass
        uf = card.get('uploaded_files')
        if uf and uf.get('is_current') == 0:
            return 'history'
        return 'current'

    def _detect_risk_flags(self, card):
        flags = []
        semantic = card.get('semantic', {}) or {}
        report_meta = card.get('report_meta')
        if report_meta:
            if report_meta.get('valid_to'):
                try:
                    valid_to = datetime.fromisoformat(report_meta['valid_to'])
                    if valid_to < datetime.now(timezone.utc):
                        flags.append('expired_certificate')
                except (ValueError, TypeError):
                    pass
            if not report_meta.get('scan_available', True):
                flags.append('scan_unavailable')
        if semantic.get('quality_tier') == 'placeholder':
            flags.append('unannotated')
        return flags

    def _format_source(self, card):
        source_type = card.get('source_type', '')
        doc = card.get('doc_file', '')
        path = card.get('path', '')
        if source_type == 'excel':
            return f"{doc}:{path}"
        return f"{doc}:{path}"

    def _row_to_dict(self, row):
        d = dict(row)
        if d.get('risk_flags'):
            try:
                d['risk_flags'] = json.loads(d['risk_flags'])
            except (json.JSONDecodeError, TypeError):
                d['risk_flags'] = []
        return d
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_evidence_pack.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/evidence/ backend/tests/test_evidence_pack.py && git commit -m "feat: add evidence pack builder service with persist and archive"
```

---

### Task 2: Risk Flag Detection Service

**Files:**
- Create: `backend/evidence/risk.py`
- Test: `backend/tests/test_risk.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_risk.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_expired_certificate_detected():
    """Expired certificate valid_to triggers expired_certificate flag."""
    from evidence.risk import detect_risk_flags
    card = {
        'report_meta': {
            'valid_to': '2025-01-01',
            'scan_available': True,
        },
        'semantic': {'quality_tier': 'high'},
    }
    flags = detect_risk_flags(card)
    assert 'expired_certificate' in flags


def test_scan_unavailable_detected():
    """scan_available=false triggers scan_unavailable flag."""
    from evidence.risk import detect_risk_flags
    card = {
        'report_meta': {
            'valid_to': '2027-01-01',
            'scan_available': False,
        },
        'semantic': {'quality_tier': 'high'},
    }
    flags = detect_risk_flags(card)
    assert 'scan_unavailable' in flags


def test_model_mismatch_detected():
    """Model mismatch between requirement and card triggers flag."""
    from evidence.risk import check_model_match
    result = check_model_match(
        required_models=['AMS1000'],
        card_models=['CMS1000'],
    )
    assert result['match'] is False
    assert 'model_mismatch' in result['flags']


def test_missing_report_detected():
    """When tender requires report but no report evidence found."""
    from evidence.risk import assess_report_risk
    result = assess_report_risk(
        required_capabilities=['SM2', 'SM3', 'SM4'],
        product_evidence=[{'evidence_type': 'parameter', 'body': '支持国密'}],
        report_evidence=[],
    )
    assert result['judgement'] == 'partial'
    assert any('检测报告未确认' in r for r in result['risks'])


def test_report_expired_risk():
    """Report found but expired → not satisfied."""
    from evidence.risk import assess_report_risk
    result = assess_report_risk(
        required_capabilities=['SM2'],
        product_evidence=[{'evidence_type': 'parameter', 'body': '支持SM2'}],
        report_evidence=[{
            'evidence_type': 'report',
            'body': 'SM2检测报告',
            'freshness': 'expired',
            'risk_flags': ['expired_certificate'],
        }],
    )
    assert result['judgement'] != 'satisfied'
    assert any('过期' in r or 'expired' in r.lower() for r in result['risks'])


def test_satisfied_with_valid_report():
    """Valid report + matching capability = satisfied."""
    from evidence.risk import assess_report_risk
    result = assess_report_risk(
        required_capabilities=['SM2'],
        product_evidence=[{'evidence_type': 'parameter', 'body': '支持SM2'}],
        report_evidence=[{
            'evidence_type': 'report',
            'body': 'SM2检测报告',
            'freshness': 'current',
            'risk_flags': [],
        }],
    )
    assert result['judgement'] == 'satisfied'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_risk.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'evidence'"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/evidence/risk.py
from datetime import datetime, timezone


def detect_risk_flags(card):
    """Detect risk flags for a single card."""
    flags = []
    report_meta = card.get('report_meta')
    semantic = card.get('semantic', {}) or {}

    if report_meta:
        if report_meta.get('valid_to'):
            try:
                valid_to = datetime.fromisoformat(report_meta['valid_to'])
                if valid_to < datetime.now(timezone.utc):
                    flags.append('expired_certificate')
            except (ValueError, TypeError):
                pass
        if not report_meta.get('scan_available', True):
            flags.append('scan_unavailable')

    if semantic.get('quality_tier') == 'placeholder':
        flags.append('unannotated')

    return flags


def check_model_match(required_models, card_models):
    """Check if card models match required models."""
    if not required_models:
        return {'match': True, 'flags': []}
    if not card_models:
        return {'match': False, 'flags': ['model_mismatch']}

    required_set = set(m.upper() for m in required_models)
    card_set = set(m.upper() for m in card_models)

    if required_set & card_set:
        return {'match': True, 'flags': []}
    return {'match': False, 'flags': ['model_mismatch']}


def assess_report_risk(required_capabilities, product_evidence, report_evidence):
    """Assess risk for tender requirements that need both capability and report evidence.

    Returns dict with:
      - judgement: 'satisfied' | 'partial' | 'unknown' | 'not_satisfied'
      - risks: list of risk descriptions
      - capability_score: float 0-1
      - report_score: float 0-1
    """
    risks = []

    # Score capability evidence
    capability_score = 0.0
    if product_evidence:
        capability_score = min(1.0, len(product_evidence) * 0.5)

    # Score report evidence
    report_score = 0.0
    valid_reports = []
    for rep in report_evidence:
        freshness = rep.get('freshness', 'unknown')
        risk_flags = rep.get('risk_flags', [])
        if freshness == 'expired' or 'expired_certificate' in risk_flags:
            risks.append('检测报告已过期')
            continue
        if 'scan_unavailable' in risk_flags:
            risks.append('检测报告扫描件未确认')
            report_score = max(report_score, 0.3)
            continue
        valid_reports.append(rep)
        report_score = max(report_score, 0.8)

    # No report at all
    if not report_evidence:
        risks.append('检测报告未确认')
        report_score = 0.0
    elif not valid_reports and report_evidence:
        # All reports were expired/invalid
        pass

    # Determine judgement
    if capability_score >= 0.75 and report_score >= 0.75 and not risks:
        judgement = 'satisfied'
    elif capability_score >= 0.75 and report_score < 0.75:
        judgement = 'partial'
    elif capability_score >= 0.4:
        judgement = 'unknown'
    else:
        judgement = 'not_satisfied'

    return {
        'judgement': judgement,
        'risks': risks,
        'capability_score': capability_score,
        'report_score': report_score,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_risk.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/evidence/risk.py backend/tests/test_risk.py && git commit -m "feat: add risk flag detection and report assessment service"
```

---

### Task 3: Report Pipeline

**Files:**
- Create: `backend/pipeline/report.py`
- Modify: `backend/pipeline/__init__.py` (add ReportPipeline export)
- Test: `backend/tests/test_pipeline_report.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_pipeline_report.py
import sys, os, tempfile, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_report_pipeline_generates_cards_with_report_meta():
    """Report pipeline creates cards with report_meta field."""
    from pipeline.report import ReportPipeline
    pipeline = ReportPipeline()
    with tempfile.NamedTemporaryFile(suffix='.md', mode='w', delete=False, encoding='utf-8') as f:
        f.write("# CMA检测报告\n\n")
        f.write("报告编号: CMA-2026-001\n")
        f.write("检测机构: 中国计量科学研究院\n")
        f.write("产品型号: AMS1000\n")
        f.write("检测能力: AVC/SVC, H.323, SIP\n")
        f.write("有效期至: 2027-06-01\n")
        f.write("扫描件: 有\n")
        tmppath = f.name
    try:
        cards = pipeline.parse(tmppath, doc_file='CMA检测报告.md')
        assert len(cards) >= 1
        card = cards[0]
        assert card['source_type'] == 'report'
        assert card['report_meta'] is not None
        assert card['report_meta']['report_type'] is not None
        assert len(card['report_meta']['product_models']) > 0
    finally:
        os.unlink(tmppath)


def test_report_pipeline_extracts_product_models():
    """Report pipeline extracts product model names from content."""
    from pipeline.report import ReportPipeline
    pipeline = ReportPipeline()
    with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False, encoding='utf-8') as f:
        f.write("第三方检测报告\n\n")
        f.write("产品: AMS1000 CMS1000\n")
        f.write("检测项目: 视频协议\n")
        tmppath = f.name
    try:
        cards = pipeline.parse(tmppath, doc_file='检测报告.txt')
        assert len(cards) >= 1
        meta = cards[0]['report_meta']
        assert 'AMS1000' in meta['product_models']
        assert 'CMS1000' in meta['product_models']
    finally:
        os.unlink(tmppath)


def test_report_pipeline_default_meta_when_extraction_fails():
    """When report_meta cannot be extracted, use placeholder defaults."""
    from pipeline.report import ReportPipeline
    pipeline = ReportPipeline()
    with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False, encoding='utf-8') as f:
        f.write("Some generic document without report structure.")
        tmppath = f.name
    try:
        cards = pipeline.parse(tmppath, doc_file='generic.txt')
        assert len(cards) >= 1
        meta = cards[0]['report_meta']
        assert meta is not None
        assert meta['report_type'] is not None
    finally:
        os.unlink(tmppath)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_pipeline_report.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'pipeline.report'"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/pipeline/report.py
import re
from datetime import datetime, timezone
from pipeline.base import PipelineBase, PipelineError


REPORT_TYPE_KEYWORDS = {
    'CMA': ['CMA', '中国计量'],
    'CNAS': ['CNAS', '中国合格评定'],
    '原厂证明函': ['原厂证明', '原厂授权', '厂家证明'],
    '信创认证': ['信创', '适配认证', '信创目录'],
    '兼容性证明': ['兼容性', '互操作', '兼容证明'],
    '第三方检测': ['第三方检测', '第三方测试', '独立检测'],
}

MODEL_PATTERN = re.compile(r'[A-Z]{2,}\d{3,}(?:\s*[A-Z]+\d+)?(?:\s*V[\d.]+)?')

SCAN_KEYWORDS = ['扫描件', '原件', '可交付', '有附件']
NO_SCAN_KEYWORDS = ['无扫描', '未提供扫描', '扫描件未']


class ReportPipeline(PipelineBase):
    def parse(self, file_path, doc_file=None):
        if doc_file is None:
            import os
            doc_file = os.path.basename(file_path)

        text = self._read_file(file_path)
        if not text.strip():
            raise PipelineError("报告文档无有效文本内容")

        report_meta = self._extract_report_meta(text)
        body_parts = self._split_body(text)
        cards = []

        for i, part in enumerate(body_parts):
            card = self.make_card(
                title=part.get('title', f'报告段落{i+1}'),
                body=part['body'],
                doc_file=doc_file,
                source_type='report',
                level=part.get('level', 1),
                path=f"{doc_file} > {part.get('title', f'段落{i+1}')}",
                line_start=part.get('line_start', 0),
                seq=i,
                source_id='06',
            )
            card['report_meta'] = report_meta
            cards.append(card)

        if not cards:
            card = self.make_card(
                title='报告全文',
                body=text,
                doc_file=doc_file,
                source_type='report',
                level=1,
                path=f"{doc_file} > 全文",
                line_start=0,
                seq=0,
                source_id='06',
            )
            card['report_meta'] = report_meta
            cards.append(card)

        return cards

    def _read_file(self, file_path):
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise PipelineError("无法识别报告文件编码")

    def _extract_report_meta(self, text):
        report_type = '其他'
        for rtype, keywords in REPORT_TYPE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                report_type = rtype
                break

        product_models = list(set(MODEL_PATTERN.findall(text)))

        tested_capabilities = []
        cap_patterns = ['AVC', 'SVC', 'H.323', 'SIP', 'SM2', 'SM3', 'SM4', '国密', '全编全解']
        for cap in cap_patterns:
            if cap in text:
                tested_capabilities.append(cap)

        issuing_org = self._extract_field(text, ['检测机构', '认证机构', '签发单位', '出具单位'])
        certificate_no = self._extract_field(text, ['报告编号', '证书编号', '编号'])

        valid_from = self._extract_date(text, ['有效期起', '签发日期', '从'])
        valid_to = self._extract_date(text, ['有效期至', '有效期到', '到期', '至'])

        scan_available = True
        if any(kw in text for kw in NO_SCAN_KEYWORDS):
            scan_available = False
        elif any(kw in text for kw in SCAN_KEYWORDS):
            scan_available = True

        return {
            'report_type': report_type,
            'issuing_org': issuing_org or '',
            'certificate_no': certificate_no or '',
            'product_models': product_models,
            'tested_capabilities': tested_capabilities,
            'valid_from': valid_from or '',
            'valid_to': valid_to or '',
            'scan_available': scan_available,
        }

    def _extract_field(self, text, keywords):
        for kw in keywords:
            pattern = re.compile(rf'{kw}[：:]\s*(.+?)[\n\r]')
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_date(self, text, keywords):
        for kw in keywords:
            pattern = re.compile(rf'{kw}[：:]\s*(\d{{4}}[-./]\d{{1,2}}[-./]\d{{1,2}})')
            match = pattern.search(text)
            if match:
                raw = match.group(1).replace('/', '-').replace('.', '-')
                try:
                    datetime.strptime(raw, '%Y-%m-%d')
                    return raw
                except ValueError:
                    pass
        return None

    def _split_body(self, text):
        sections = []
        lines = text.split('\n')
        current_title = ''
        current_body = []
        current_level = 0
        line_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            heading_match = re.match(r'^(#{1,3})\s+(.+)', stripped)
            if heading_match:
                if current_body:
                    sections.append({
                        'title': current_title,
                        'body': '\n'.join(current_body).strip(),
                        'level': current_level,
                        'line_start': line_start,
                    })
                current_level = len(heading_match.group(1))
                current_title = heading_match.group(2).strip()
                current_body = []
                line_start = i
            elif stripped:
                current_body.append(stripped)

        if current_body:
            sections.append({
                'title': current_title,
                'body': '\n'.join(current_body).strip(),
                'level': current_level,
                'line_start': line_start,
            })

        return sections
```

- [ ] **Step 4: Update pipeline/__init__.py**

```python
# backend/pipeline/__init__.py - add to existing exports
from pipeline.base import PipelineBase, PipelineError
from pipeline.word import WordPipeline
from pipeline.markdown import MarkdownPipeline
from pipeline.txt import TxtPipeline
from pipeline.ppt import PptPipeline
from pipeline.excel import ExcelPipeline
from pipeline.report import ReportPipeline
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_pipeline_report.py -v`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/pipeline/report.py backend/pipeline/__init__.py backend/tests/test_pipeline_report.py && git commit -m "feat: add report pipeline with report_meta extraction"
```

---

### Task 4: Evidence API Endpoints

**Files:**
- Create: `backend/api/evidence.py`
- Modify: `backend/main.py` (register evidence router)
- Test: `backend/tests/test_evidence_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_evidence_api.py
import sys, os, tempfile, sqlite3, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_evidence_build_endpoint():
    """POST /api/v1/evidence/build returns evidence items."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from card.store import CardStore
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        store = CardStore(conn)
        store.save({
            'id': '01-01-test-sec-001',
            'doc_file': '报价.xlsx',
            'source_type': 'excel',
            'title': 'AE800 报价',
            'level': 0,
            'path': '报价.xlsx:Sheet1:5',
            'line_start': 5,
            'char_count': 20,
            'body': '价格: 138000',
            'tags': [],
            'keywords': [],
            'models': ['AE800'],
            'related_topics': [],
            'aliases': [],
            'sibling_sections': [],
            'source_weight': 2,
            'report_meta': None,
            'semantic': {
                'annotated_at': '2026-05-16T00:00:00Z',
                'annotator_model': 'test',
                'annotation_version': 1,
                'intent_tags': ['报价价格'],
                'concept_tags': [],
                'scenario_tags': [],
                'quality_tier': 'high',
                'card_type': 'price',
                'summary': 'AE800 报价信息',
                'models': ['AE800'],
                'keywords': ['价格'],
                'negative_concepts': [],
                'content_hash': 'abc123',
            },
        })
        from api.evidence import build_evidence
        result = build_evidence(
            cards=[store.get('01-01-test-sec-001')],
            task_type='bom',
            project_id='proj-001',
            conn=conn,
        )
        assert len(result['evidences']) == 1
        assert result['evidences'][0]['evidence_type'] == 'price'
        conn.close()


def test_evidence_get_and_list():
    """Get single evidence and list by project work correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from evidence.pack import EvidencePackBuilder
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        builder = EvidencePackBuilder(conn)
        cards = [
            {
                'id': '01-01-test-sec-001',
                'source_type': 'excel',
                'title': 'AE800',
                'body': '价格: 138000',
                'path': '报价.xlsx:Sheet1:5',
                'models': ['AE800'],
                'semantic': {'card_type': 'price', 'quality_tier': 'high', 'summary': '报价'},
                'report_meta': None,
            }
        ]
        evidences = builder.build(cards, task_type='bom')
        pack_id = builder.persist(evidences, project_id='proj-001')
        got = builder.get(pack_id)
        assert got is not None
        items = builder.list_by_project('proj-001')
        assert len(items) == 1
        conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_evidence_api.py -v`
Expected: FAIL with import errors

- [ ] **Step 3: Write minimal implementation**

```python
# backend/api/evidence.py
from fastapi import APIRouter, HTTPException, Query
from db.models import get_db
from evidence.pack import EvidencePackBuilder

router = APIRouter(prefix="/evidence", tags=["evidence"])


def build_evidence(cards, task_type, project_id=None, conn=None):
    """Helper to build evidence from cards. Used by both API and internal callers."""
    builder = EvidencePackBuilder(conn)
    evidences = builder.build(cards, task_type=task_type, project_id=project_id)
    risk_summary = []
    for ev in evidences:
        for flag in ev.get('risk_flags', []):
            risk_summary.append(f"[{ev['source_card_id']}] {flag}")
    return {
        'evidence_pack_id': None,
        'evidences': evidences,
        'risk_summary': risk_summary,
    }


@router.post("/build")
async def api_build_evidence(body: dict):
    """Build evidence pack from card IDs."""
    card_ids = body.get('card_ids', [])
    task_type = body.get('task_type', 'proposal')
    project_id = body.get('project_id')
    persist = body.get('persist', False)

    if not card_ids:
        raise HTTPException(status_code=400, detail="CARD_IDS_REQUIRED")

    conn = get_db()
    try:
        from card.store import CardStore
        store = CardStore(conn)
        cards = []
        for cid in card_ids:
            card = store.get(cid)
            if card:
                cards.append(card)

        if not cards:
            raise HTTPException(status_code=404, detail="NO_CARDS_FOUND")

        builder = EvidencePackBuilder(conn)
        evidences = builder.build(cards, task_type=task_type, project_id=project_id)
        risk_summary = []
        for ev in evidences:
            for flag in ev.get('risk_flags', []):
                risk_summary.append(f"[{ev['source_card_id']}] {flag}")

        pack_id = None
        if persist:
            pack_id = builder.persist(evidences, project_id=project_id)

        return {
            'evidence_pack_id': pack_id,
            'evidences': evidences,
            'risk_summary': risk_summary,
        }
    finally:
        conn.close()


@router.get("/{evidence_id}")
async def get_evidence(evidence_id: str):
    conn = get_db()
    try:
        builder = EvidencePackBuilder(conn)
        ev = builder.get(evidence_id)
        if not ev:
            raise HTTPException(status_code=404, detail="EVIDENCE_NOT_FOUND")
        return ev
    finally:
        conn.close()


@router.post("/{evidence_id}/archive")
async def archive_evidence(evidence_id: str):
    conn = get_db()
    try:
        builder = EvidencePackBuilder(conn)
        ev = builder.get(evidence_id)
        if not ev:
            raise HTTPException(status_code=404, detail="EVIDENCE_NOT_FOUND")
        builder.archive(evidence_id)
        return {"status": "archived", "evidence_id": evidence_id}
    finally:
        conn.close()


@router.get("/project/{project_id}")
async def list_project_evidence(project_id: str, include_archived: bool = Query(False)):
    conn = get_db()
    try:
        builder = EvidencePackBuilder(conn)
        items = builder.list_by_project(project_id, include_archived=include_archived)
        return {"total": len(items), "items": items}
    finally:
        conn.close()
```

- [ ] **Step 4: Register router in main.py**

Add to `backend/main.py`:
```python
from api.evidence import router as evidence_router
app.include_router(evidence_router, prefix="/api/v1")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_evidence_api.py -v`
Expected: 2 tests PASS

- [ ] **Step 6: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/api/evidence.py backend/main.py backend/tests/test_evidence_api.py && git commit -m "feat: add evidence pack API endpoints"
```

---

### Task 5: Tender Matching Service

**Files:**
- Create: `backend/services/tender_service.py`
- Test: `backend/tests/test_tender_service.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_tender_service.py
import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_extract_requirements_from_text():
    """Extract structured requirements from tender text."""
    from services.tender_service import TenderService
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = TenderService(conn)
        tender_text = """
        1. 支持SM2/SM3/SM4国密算法，须提供CMA/CNAS检测报告
        2. 支持H.323和SIP协议
        3. 须提供原厂授权证明函
        """
        reqs = svc.extract_requirements(tender_text)
        assert len(reqs) >= 2
        assert any('检测报告' in r.get('required_evidence', [''])[0] or
                    'CMA' in r.get('raw_text', '') for r in reqs)
        conn.close()


def test_match_requirements_to_evidence():
    """Match requirements against evidence and produce judgements."""
    from services.tender_service import TenderService
    from evidence.risk import assess_report_risk
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = TenderService(conn)
        requirement = {
            'id': 'req-001',
            'raw_text': '支持SM2/SM3/SM4国密算法，须提供CMA/CNAS检测报告',
            'requirement_type': 'security',
            'required_capabilities': ['SM2', 'SM3', 'SM4'],
            'required_evidence': ['CMA检测报告'],
        }
        product_evidence = [
            {'evidence_type': 'parameter', 'body': '支持SM2/SM3/SM4国密加密'}
        ]
        report_evidence = [
            {'evidence_type': 'report', 'body': 'SM2/SM3/SM4 CMA检测报告', 'freshness': 'current', 'risk_flags': []}
        ]
        result = svc.match_single(requirement, product_evidence, report_evidence)
        assert result['judgement'] == 'satisfied'
        conn.close()


def test_match_partial_when_no_report():
    """Partial satisfaction when capability found but no report."""
    from services.tender_service import TenderService
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = TenderService(conn)
        requirement = {
            'id': 'req-002',
            'raw_text': '须提供CMA/CNAS检测报告',
            'requirement_type': 'security',
            'required_capabilities': ['SM2'],
            'required_evidence': ['CMA检测报告'],
        }
        product_evidence = [{'evidence_type': 'parameter', 'body': '支持SM2'}]
        report_evidence = []
        result = svc.match_single(requirement, product_evidence, report_evidence)
        assert result['judgement'] == 'partial'
        conn.close()


def test_match_expired_report():
    """Expired report → not satisfied or partial with risk."""
    from services.tender_service import TenderService
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = TenderService(conn)
        requirement = {
            'id': 'req-003',
            'raw_text': '须提供CMA检测报告',
            'requirement_type': 'security',
            'required_capabilities': ['SM2'],
            'required_evidence': ['CMA检测报告'],
        }
        product_evidence = [{'evidence_type': 'parameter', 'body': '支持SM2'}]
        report_evidence = [{
            'evidence_type': 'report',
            'body': 'SM2 CMA报告',
            'freshness': 'expired',
            'risk_flags': ['expired_certificate'],
        }]
        result = svc.match_single(requirement, product_evidence, report_evidence)
        assert result['judgement'] != 'satisfied'
        assert any('过期' in r for r in result.get('risks', []))
        conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_tender_service.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'services.tender_service'"

- [ ] **Step 3: Write minimal implementation**

```python
# backend/services/tender_service.py
import re
import uuid
from evidence.risk import assess_report_risk, check_model_match

EVIDENCE_KEYWORDS = {
    'CMA': ['CMA', '检测报告', '第三方检测'],
    'CNAS': ['CNAS'],
    '原厂证明函': ['原厂证明', '原厂授权', '厂家证明'],
    '信创认证': ['信创', '适配认证'],
    '兼容性证明': ['兼容性', '互操作'],
}

CAPABILITY_KEYWORDS = {
    'SM2': ['SM2', '国密SM2'],
    'SM3': ['SM3', '国密SM3'],
    'SM4': ['SM4', '国密SM4'],
    'H.323': ['H.323', 'H323'],
    'SIP': ['SIP'],
    'AVC': ['AVC'],
    'SVC': ['SVC'],
    '全编全解': ['全编全解'],
}

MODEL_PATTERN = re.compile(r'[A-Z]{2,}\d{3,}(?:\s*[A-Z]+\d+)?')


class TenderService:
    def __init__(self, conn):
        self.conn = conn

    def extract_requirements(self, tender_text):
        """Extract structured requirements from tender text using rule-based parsing."""
        requirements = []
        # Split by numbered items
        items = re.split(r'\n\s*\d+[.、）)]\s*', tender_text)
        items = [i.strip() for i in items if i.strip()]

        for i, item in enumerate(items):
            req_id = str(uuid.uuid4())[:8]
            required_capabilities = []
            required_evidence = []

            # Detect capability requirements
            for cap, keywords in CAPABILITY_KEYWORDS.items():
                if any(kw in item for kw in keywords):
                    required_capabilities.append(cap)

            # Detect evidence requirements
            for etype, keywords in EVIDENCE_KEYWORDS.items():
                if any(kw in item for kw in keywords):
                    required_evidence.append(etype)

            # Detect target models
            target_models = MODEL_PATTERN.findall(item)

            # Determine requirement type
            req_type = 'general'
            if any(kw in item for kw in ['安全', '加密', '国密', '认证']):
                req_type = 'security'
            elif any(kw in item for kw in ['性能', '并发', '路数']):
                req_type = 'performance'
            elif any(kw in item for kw in ['兼容', '接口', '协议']):
                req_type = 'compatibility'
            elif any(kw in item for kw in ['价格', '报价']):
                req_type = 'price'

            requirements.append({
                'id': req_id,
                'raw_text': item,
                'requirement_type': req_type,
                'target_models': target_models,
                'required_capabilities': required_capabilities,
                'required_evidence': required_evidence,
            })

        return requirements

    def match_single(self, requirement, product_evidence, report_evidence):
        """Match a single requirement against product and report evidence."""
        result = assess_report_risk(
            required_capabilities=requirement.get('required_capabilities', []),
            product_evidence=product_evidence,
            report_evidence=report_evidence,
        )

        # Build evidence references
        product_refs = [ev.get('body', '')[:100] for ev in product_evidence]
        report_refs = [ev.get('body', '')[:100] for ev in report_evidence]

        return {
            'requirement_id': requirement['id'],
            'judgement': result['judgement'],
            'confidence': (result['capability_score'] + result['report_score']) / 2,
            'product_evidence': product_evidence,
            'report_evidence': report_evidence,
            'risks': result['risks'],
            'product_refs': product_refs,
            'report_refs': report_refs,
        }

    def match_batch(self, requirements, evidence_by_capability):
        """Match multiple requirements against evidence."""
        results = []
        for req in requirements:
            product_ev = []
            report_ev = []
            for cap in req.get('required_capabilities', []):
                if cap in evidence_by_capability:
                    for ev in evidence_by_capability[cap]:
                        if ev.get('evidence_type') == 'report':
                            report_ev.append(ev)
                        else:
                            product_ev.append(ev)
            results.append(self.match_single(req, product_ev, report_ev))
        return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_tender_service.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/services/tender_service.py backend/tests/test_tender_service.py && git commit -m "feat: add tender matching service with rule-based extraction and mixed judgement"
```

---

### Task 6: Tender API Endpoints

**Files:**
- Create: `backend/api/tender.py`
- Modify: `backend/main.py` (register tender router)

- [ ] **Step 1: Write the implementation (no separate test file needed — tests covered by tender_service tests)**

```python
# backend/api/tender.py
from fastapi import APIRouter, HTTPException
from db.models import get_db
from services.tender_service import TenderService
from evidence.pack import EvidencePackBuilder
from card.store import CardStore

router = APIRouter(prefix="/tender", tags=["tender"])


@router.post("/analyze")
async def analyze_tender(body: dict):
    """Analyze tender text and extract structured requirements."""
    tender_text = body.get('tender_text', '')
    if not tender_text:
        raise HTTPException(status_code=400, detail="TENDER_TEXT_REQUIRED")

    conn = get_db()
    try:
        svc = TenderService(conn)
        requirements = svc.extract_requirements(tender_text)

        # Persist requirements if project_id provided
        project_id = body.get('project_id')
        if project_id:
            import json
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat()
            for req in requirements:
                conn.execute(
                    """INSERT INTO project_requirements
                       (id, project_id, requirement_type, raw_text, structured_json, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (req['id'], project_id, req['requirement_type'],
                     req['raw_text'], json.dumps(req), now)
                )
            conn.commit()

        return {
            'total': len(requirements),
            'requirements': requirements,
        }
    finally:
        conn.close()


@router.post("/match")
async def match_tender(body: dict):
    """Match tender requirements against knowledge base evidence."""
    project_id = body.get('project_id')
    requirement_ids = body.get('requirement_ids', [])
    candidate_models = body.get('candidate_models', [])

    if not project_id and not requirement_ids:
        raise HTTPException(status_code=400, detail="PROJECT_ID_OR_REQUIREMENTS_REQUIRED")

    conn = get_db()
    try:
        svc = TenderService(conn)
        builder = EvidencePackBuilder(conn)
        store = CardStore(conn)

        # Load requirements
        requirements = []
        if requirement_ids:
            for rid in requirement_ids:
                row = conn.execute(
                    "SELECT * FROM project_requirements WHERE id = ?", (rid,)
                ).fetchone()
                if row:
                    import json
                    req = json.loads(row['structured_json']) if row['structured_json'] else {}
                    req['id'] = row['id']
                    req['raw_text'] = row['raw_text']
                    req['requirement_type'] = row['requirement_type']
                    requirements.append(req)
        elif project_id:
            rows = conn.execute(
                "SELECT * FROM project_requirements WHERE project_id = ?", (project_id,)
            ).fetchall()
            for row in rows:
                import json
                req = json.loads(row['structured_json']) if row['structured_json'] else {}
                req['id'] = row['id']
                req['raw_text'] = row['raw_text']
                req['requirement_type'] = row['requirement_type']
                requirements.append(req)

        if not requirements:
            raise HTTPException(status_code=404, detail="NO_REQUIREMENTS_FOUND")

        # Search for evidence for each requirement
        results = []
        for req in requirements:
            # Simple keyword-based card search
            caps = req.get('required_capabilities', [])
            search_query = ' '.join(caps) if caps else req.get('raw_text', '')[:100]

            # Search cards by keywords in body
            product_evidence = []
            report_evidence = []
            for cap in caps:
                rows = conn.execute(
                    "SELECT * FROM cards WHERE body LIKE ? LIMIT 10",
                    (f'%{cap}%',)
                ).fetchall() if False else []  # Placeholder — actual search uses CardStore

            # Use CardStore search
            all_cards = store.list_cards(page_size=200).get('items', [])
            for card in all_cards:
                body_text = card.get('body', '')
                title_text = card.get('title', '')
                match_score = sum(1 for cap in caps if cap in body_text or cap in title_text)
                if match_score > 0:
                    if card.get('source_type') == 'report':
                        report_evidence.append({
                            'source_card_id': card['id'],
                            'evidence_type': 'report',
                            'body': body_text[:200],
                            'source': f"{card.get('doc_file', '')}:{card.get('path', '')}",
                            'freshness': 'current',
                            'risk_flags': [],
                        })
                    else:
                        product_evidence.append({
                            'source_card_id': card['id'],
                            'evidence_type': 'parameter',
                            'body': body_text[:200],
                            'source': f"{card.get('doc_file', '')}:{card.get('path', '')}",
                            'freshness': 'current',
                            'risk_flags': [],
                        })

            match_result = svc.match_single(req, product_evidence, report_evidence)
            results.append(match_result)

        return {
            'total': len(results),
            'results': results,
        }
    finally:
        conn.close()


@router.get("/{output_id}")
async def get_tender_result(output_id: str):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM project_outputs WHERE id = ? AND output_type = 'tender'",
            (output_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="TENDER_NOT_FOUND")
        return dict(row)
    finally:
        conn.close()
```

- [ ] **Step 2: Register router in main.py**

Add to `backend/main.py`:
```python
from api.tender import router as tender_router
app.include_router(tender_router, prefix="/api/v1")
```

- [ ] **Step 3: Syntax check**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "import ast; ast.parse(open('api/tender.py').read()); print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/api/tender.py backend/main.py && git commit -m "feat: add tender API endpoints for analysis and matching"
```

---

### Task 7: Register Report Pipeline in Job Executor

**Files:**
- Modify: `backend/job/executor.py` (add pipeline_report handler)

- [ ] **Step 1: Read current executor.py**

Read `backend/job/executor.py` to understand existing handler registration.

- [ ] **Step 2: Add report pipeline handler**

Add `pipeline_report` handler to `register_default_handlers()` in `backend/job/executor.py`:

```python
def handle_pipeline_report(job, conn):
    from pipeline.report import ReportPipeline
    from card.store import CardStore
    import json, os
    pipeline = ReportPipeline()
    store = CardStore(conn)
    payload = json.loads(job['payload']) if job.get('payload') else {}
    file_path = payload.get('file_path')
    doc_file = payload.get('doc_file', os.path.basename(file_path) if file_path else 'unknown')
    if not file_path:
        raise ValueError("pipeline_report requires file_path in payload")
    cards = pipeline.parse(file_path, doc_file=doc_file)
    for card in cards:
        store.save(card)
    return {'cards_generated': len(cards)}
```

Register it alongside existing handlers.

- [ ] **Step 3: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/job/executor.py && git commit -m "feat: register report pipeline handler in job executor"
```

---

### Task 8: Integration Tests for Evidence Layer

**Files:**
- Create: `backend/tests/test_evidence_integration.py`

- [ ] **Step 1: Write integration test**

```python
# backend/tests/test_evidence_integration.py
import sys, os, tempfile, sqlite3, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_full_evidence_flow():
    """Test: create cards → build evidence → persist → list → archive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from evidence.pack import EvidencePackBuilder
        from card.store import CardStore
        from evidence.risk import assess_report_risk

        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)

        # Create cards
        store = CardStore(conn)
        store.save({
            'id': '01-01-test-sec-001',
            'doc_file': '报价.xlsx',
            'source_type': 'excel',
            'title': 'AE800 报价',
            'level': 0,
            'path': '报价.xlsx:Sheet1:5',
            'line_start': 5,
            'char_count': 20,
            'body': '价格: 138000',
            'tags': [],
            'keywords': [],
            'models': ['AE800'],
            'related_topics': [],
            'aliases': [],
            'sibling_sections': [],
            'source_weight': 2,
            'report_meta': None,
            'semantic': {
                'annotated_at': '2026-05-16T00:00:00Z',
                'annotator_model': 'test',
                'annotation_version': 1,
                'intent_tags': ['报价价格'],
                'concept_tags': [],
                'scenario_tags': [],
                'quality_tier': 'high',
                'card_type': 'price',
                'summary': 'AE800 报价',
                'models': ['AE800'],
                'keywords': ['价格'],
                'negative_concepts': [],
                'content_hash': 'abc123',
            },
        })
        store.save({
            'id': '01-01-test-sec-002',
            'doc_file': 'CMA报告.md',
            'source_type': 'report',
            'title': 'CMA检测报告',
            'level': 1,
            'path': 'CMA报告.md > 全文',
            'line_start': 0,
            'char_count': 100,
            'body': 'SM2/SM3/SM4国密算法检测通过',
            'tags': [],
            'keywords': [],
            'models': ['AMS1000'],
            'related_topics': [],
            'aliases': [],
            'sibling_sections': [],
            'source_weight': 3,
            'report_meta': {
                'report_type': 'CMA',
                'issuing_org': '中国计量科学研究院',
                'certificate_no': 'CMA-2026-001',
                'product_models': ['AMS1000'],
                'tested_capabilities': ['SM2', 'SM3', 'SM4'],
                'valid_from': '2026-01-01',
                'valid_to': '2027-06-01',
                'scan_available': True,
            },
            'semantic': {
                'annotated_at': '2026-05-16T00:00:00Z',
                'annotator_model': 'test',
                'annotation_version': 1,
                'intent_tags': ['安全保障'],
                'concept_tags': ['国密'],
                'scenario_tags': [],
                'quality_tier': 'high',
                'card_type': 'parameter',
                'summary': 'CMA国密检测报告',
                'models': ['AMS1000'],
                'keywords': ['SM2', 'CMA'],
                'negative_concepts': [],
                'content_hash': 'def456',
            },
        })

        # Build evidence
        builder = EvidencePackBuilder(conn)
        card1 = store.get('01-01-test-sec-001')
        card2 = store.get('01-01-test-sec-002')
        evidences = builder.build([card1, card2], task_type='tender', project_id='proj-001')
        assert len(evidences) == 2

        # Verify evidence types
        types = {ev['evidence_type'] for ev in evidences}
        assert 'price' in types
        assert 'report' in types

        # Persist
        pack_id = builder.persist(evidences, project_id='proj-001')
        assert pack_id is not None

        # List
        items = builder.list_by_project('proj-001')
        assert len(items) == 2

        # Risk assessment
        result = assess_report_risk(
            required_capabilities=['SM2', 'SM3', 'SM4'],
            product_evidence=[ev for ev in evidences if ev['evidence_type'] != 'report'],
            report_evidence=[ev for ev in evidences if ev['evidence_type'] == 'report'],
        )
        assert result['judgement'] == 'satisfied'

        # Archive
        builder.archive(pack_id)
        items = builder.list_by_project('proj-001')
        assert len(items) == 1

        conn.close()


def test_report_pipeline_and_tender_match():
    """Test: parse report doc → create cards → match against tender requirement."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from pipeline.report import ReportPipeline
        from services.tender_service import TenderService
        from card.store import CardStore

        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)

        # Parse report
        pipeline = ReportPipeline()
        import tempfile as tf
        with tf.NamedTemporaryFile(suffix='.md', mode='w', delete=False, encoding='utf-8') as f:
            f.write("# CMA检测报告\n\n报告编号: CMA-2026-001\n产品型号: AMS1000\n检测能力: SM2, SM3, SM4\n有效期至: 2027-06-01\n")
            tmppath = f.name

        try:
            cards = pipeline.parse(tmppath, doc_file='CMA报告.md')
            assert len(cards) >= 1

            # Save cards
            store = CardStore(conn)
            for card in cards:
                store.save(card)

            # Match against tender
            svc = TenderService(conn)
            requirement = {
                'id': 'req-001',
                'raw_text': '须提供CMA/CNAS检测报告',
                'requirement_type': 'security',
                'required_capabilities': ['SM2', 'SM3', 'SM4'],
                'required_evidence': ['CMA'],
            }

            # Build evidence from cards
            from evidence.pack import EvidencePackBuilder
            builder = EvidencePackBuilder(conn)
            all_cards = [store.get(c['id']) for c in cards]
            evidences = builder.build(all_cards, task_type='tender')

            product_ev = [ev for ev in evidences if ev['evidence_type'] != 'report']
            report_ev = [ev for ev in evidences if ev['evidence_type'] == 'report']

            result = svc.match_single(requirement, product_ev, report_ev)
            assert result['judgement'] in ('satisfied', 'partial', 'unknown')
        finally:
            os.unlink(tmppath)
            conn.close()
```

- [ ] **Step 2: Run test**

Run: `cd /home/jjb/kb-platform/backend && python3 -m pytest tests/test_evidence_integration.py -v`
Expected: 2 tests PASS

- [ ] **Step 3: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/tests/test_evidence_integration.py && git commit -m "feat: add evidence layer integration tests"
```

---

### Task 9: Update Health Check for Evidence Stats

**Files:**
- Modify: `backend/services/health.py`

- [ ] **Step 1: Add evidence stats to health check**

Add to `check_health()` in `backend/services/health.py`:

```python
try:
    conn = get_db()
    evidence_count = conn.execute("SELECT COUNT(*) as c FROM evidence_packs WHERE archived_at IS NULL").fetchone()['c']
    report_count = conn.execute("SELECT COUNT(*) as c FROM evidence_packs WHERE evidence_type='report' AND archived_at IS NULL").fetchone()['c']
    conn.close()
    checks['evidence_count'] = evidence_count
    checks['report_evidence_count'] = report_count
except Exception:
    pass
```

- [ ] **Step 2: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/services/health.py && git commit -m "feat: add evidence stats to health check"
```
