"""
Integration tests for the Evidence Layer.

Tests cover:
1. Full evidence flow: cards -> build -> persist -> risk assessment -> archive
2. Report pipeline parsing + tender matching
"""
import tempfile
import os
import sqlite3
import importlib
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.models import init_db, get_db


def _make_semantic(intent_tags=None, quality_tier="high", summary=""):
    """Helper to create a semantic annotation dict."""
    return {
        "annotated_at": "2026-01-01T00:00:00Z",
        "annotator_model": "test-model",
        "annotation_version": "1.0",
        "intent_tags": intent_tags or [],
        "concept_tags": [],
        "scenario_tags": [],
        "quality_tier": quality_tier,
        "card_type": "parameter",
        "summary": summary,
        "models": [],
        "keywords": [],
        "negative_concepts": [],
        "content_hash": "abc123def456",
    }


def test_full_evidence_flow():
    """Test: create cards -> build evidence -> persist -> risk assess -> archive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir

        db_path = os.path.join(tmpdir, "test.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        init_db(conn)

        import db.models
        original_db_path = db.models.DB_PATH
        db.models.DB_PATH = db_path

        original_get_db = db.models.get_db

        class _FakeConn:
            """Wrapper that delegates to the real connection but ignores close()."""
            def __init__(self, real_conn):
                self._conn = real_conn

            def cursor(self):
                return self._conn.cursor()

            def commit(self):
                return self._conn.commit()

            def close(self):
                pass  # do not close the test connection

            def execute(self, *args, **kwargs):
                return self._conn.execute(*args, **kwargs)

            @property
            def row_factory(self):
                return self._conn.row_factory

            @row_factory.setter
            def row_factory(self, value):
                self._conn.row_factory = value

        fake_conn = _FakeConn(conn)
        db.models.get_db = lambda: fake_conn

        try:
            evidence = importlib.import_module('evidence.pack')
            risk = importlib.import_module('evidence.risk')
            store_mod = importlib.import_module('card.store')

            PROJECT_ID = "proj-test-001"
            PRICE_CARD_ID = "card-price-001"
            REPORT_CARD_ID = "card-report-001"

            # ------------------------------------------------------------------
            # Create cards
            # ------------------------------------------------------------------
            price_card = {
                "id": PRICE_CARD_ID,
                "doc_file": "price_list.xlsx",
                "source_type": "excel",
                "title": "AMS1000 终端报价",
                "level": 0,
                "path": "price_list.xlsx > Sheet1",
                "line_start": 0,
                "char_count": 50,
                "body": "AMS1000 终端含税价格 12800元/台",
                "tags": ["价格", "终端", "SM2", "SM3", "SM4"],
                "keywords": ["AMS1000", "价格", "终端", "SM2", "SM3", "SM4"],
                "models": ["AMS1000"],
                "related_topics": ["报价", "国密"],
                "aliases": [],
                "sibling_sections": [],
                "source_weight": 3,
                "report_meta": None,
                "type": "price",
                "semantic": _make_semantic(
                    intent_tags=["price_query"],
                    quality_tier="high",
                    summary="AMS1000 terminal unit price",
                ),
            }

            report_card = {
                "id": REPORT_CARD_ID,
                "doc_file": "CMA_report.pdf",
                "source_type": "report",
                "title": "CMA检测报告 - AMS1000",
                "level": 0,
                "path": "CMA_report.pdf > 检测结论",
                "line_start": 0,
                "char_count": 200,
                "body": "AMS1000终端通过CMA检测，支持SM2/SM3/SM4国密算法",
                "tags": ["CMA", "SM2", "SM3", "SM4"],
                "keywords": ["CMA", "SM2", "SM3", "SM4", "AMS1000", "检测报告"],
                "models": ["AMS1000"],
                "related_topics": ["国密", "检测"],
                "aliases": [],
                "sibling_sections": [],
                "source_weight": 3,
                "report_meta": {
                    "report_type": "CMA",
                    "issuing_org": "测试机构",
                    "certificate_no": "CMA-2026-001",
                    "product_models": ["AMS1000"],
                    "tested_capabilities": ["SM2", "SM3", "SM4"],
                    "valid_from": "2026-01-01",
                    "valid_to": "2027-06-01",
                    "scan_available": True,
                },
                "semantic": _make_semantic(
                    intent_tags=["capability_query", "report"],
                    quality_tier="high",
                    summary="CMA report for AMS1000 with SM2/SM3/SM4",
                ),
            }

            card_store = store_mod.CardStore(tmpdir)
            card_store.save(price_card)
            card_store.save(report_card)

            retrieved_price = card_store.get(PRICE_CARD_ID)
            retrieved_report = card_store.get(REPORT_CARD_ID)
            assert retrieved_price is not None, "Price card should be retrievable"
            assert retrieved_report is not None, "Report card should be retrievable"

            # ------------------------------------------------------------------
            # Build evidence
            # ------------------------------------------------------------------
            builder = evidence.EvidencePackBuilder()
            evidences = builder.build(
                cards=[price_card, report_card],
                task_type="tender",
                project_id=PROJECT_ID,
            )
            assert len(evidences) == 2, f"Expected 2 evidence items, got {len(evidences)}"

            ev_types = sorted([e["evidence_type"] for e in evidences])
            assert ev_types == ["price", "report"], f"Evidence types: {ev_types}"

            price_ev = [e for e in evidences if e["evidence_type"] == "price"][0]
            report_ev = [e for e in evidences if e["evidence_type"] == "report"][0]
            assert price_ev["project_id"] == PROJECT_ID
            assert report_ev["project_id"] == PROJECT_ID

            # ------------------------------------------------------------------
            # Persist evidence
            # ------------------------------------------------------------------
            pack_id = builder.persist(evidences, project_id=PROJECT_ID)
            assert pack_id is not None, "persist() should return a pack_id"

            retrieved_ev = builder.get(pack_id)
            assert retrieved_ev is not None, "get() should return persisted evidence"

            project_evidences = builder.list_by_project(PROJECT_ID)
            assert len(project_evidences) == 2, f"Expected 2, got {len(project_evidences)}"

            # ------------------------------------------------------------------
            # Risk assessment
            # ------------------------------------------------------------------
            result = risk.assess_report_risk(
                required_capabilities=["SM2", "SM3", "SM4"],
                product_evidence=[price_card],
                report_evidence=[report_card],
            )
            assert result["capability_score"] >= 0.6, (
                f"capability_score={result['capability_score']}"
            )
            assert result["report_score"] > 0, (
                f"report_score={result['report_score']}"
            )
            assert result["judgement"] == "satisfied", (
                f"Expected 'satisfied', got '{result['judgement']}': {result['message']}"
            )

            # ------------------------------------------------------------------
            # Archive and verify
            # ------------------------------------------------------------------
            archived = builder.archive(price_ev["id"])
            assert archived is True, "archive() should return True for existing evidence"

            active_evidences = builder.list_by_project(PROJECT_ID)
            assert len(active_evidences) == 1, (
                f"Expected 1 active, got {len(active_evidences)}"
            )
            assert active_evidences[0]["evidence_type"] == "report"

            all_evidences = builder.list_by_project(PROJECT_ID, include_archived=True)
            assert len(all_evidences) == 2, (
                f"Expected 2 total, got {len(all_evidences)}"
            )

        finally:
            db.models.get_db = original_get_db
            db.models.DB_PATH = original_db_path
            conn.close()


def test_report_pipeline_and_tender_match():
    """Test: parse CMA report -> save cards -> build evidence -> tender match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir

        db_path = os.path.join(tmpdir, "test.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        init_db(conn)

        import db.models
        original_db_path = db.models.DB_PATH
        db.models.DB_PATH = db_path

        original_get_db = db.models.get_db

        class _FakeConn:
            def __init__(self, real_conn):
                self._conn = real_conn

            def cursor(self):
                return self._conn.cursor()

            def commit(self):
                return self._conn.commit()

            def close(self):
                pass

            def execute(self, *args, **kwargs):
                return self._conn.execute(*args, **kwargs)

            @property
            def row_factory(self):
                return self._conn.row_factory

            @row_factory.setter
            def row_factory(self, value):
                self._conn.row_factory = value

        fake_conn = _FakeConn(conn)
        db.models.get_db = lambda: fake_conn

        try:
            evidence = importlib.import_module('evidence.pack')
            risk = importlib.import_module('evidence.risk')
            store_mod = importlib.import_module('card.store')
            pipeline_mod = importlib.import_module('pipeline.report')
            tender_mod = importlib.import_module('services.tender_service')

            # ------------------------------------------------------------------
            # Create a temp CMA report markdown file
            # ------------------------------------------------------------------
            report_content = """# CMA检验检测报告

检测机构：测试机构
报告编号：CMA-2026-001

## 产品信息

产品型号：AMS1000
测试项目：SM2/SM3/SM4国密算法支持测试

## 检测结论

该终端通过CMA检测认证，支持SM2、SM3、SM4国密算法。
检测日期：2026-01-01
有效期至：2027-06-01

扫描件见附件。
"""
            report_path = os.path.join(tmpdir, "cma_report.md")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            # ------------------------------------------------------------------
            # Parse with ReportPipeline
            # ------------------------------------------------------------------
            pipeline = pipeline_mod.ReportPipeline(data_dir=tmpdir)
            cards = pipeline.parse(report_path, doc_file="cma_report.md")
            assert len(cards) > 0, "parse() should return at least one card"

            report_meta = cards[0].get("report_meta")
            assert report_meta is not None, "Cards should have report_meta"
            assert report_meta["report_type"] == "CMA", (
                f"report_type={report_meta['report_type']}"
            )
            assert report_meta["issuing_org"] == "测试机构", (
                f"issuing_org={report_meta['issuing_org']}"
            )
            assert report_meta["certificate_no"] == "CMA-2026-001", (
                f"certificate_no={report_meta['certificate_no']}"
            )
            assert "AMS1000" in report_meta["product_models"], (
                f"product_models={report_meta['product_models']}"
            )
            tested = report_meta["tested_capabilities"]
            for cap in ["SM2", "SM3", "SM4"]:
                assert cap in tested, f"{cap} not in tested_capabilities: {tested}"

            # ------------------------------------------------------------------
            # Save parsed cards to CardStore
            # ------------------------------------------------------------------
            card_store = store_mod.CardStore(tmpdir)
            card_store.save_batch(cards)

            listed = card_store.list_cards()
            assert listed["total"] >= len(cards), (
                f"Expected at least {len(cards)} cards, got {listed['total']}"
            )

            reloaded_card = card_store.get(cards[0]["id"])
            assert reloaded_card is not None
            assert reloaded_card["report_meta"]["report_type"] == "CMA"

            # ------------------------------------------------------------------
            # Build evidence from parsed cards
            # ------------------------------------------------------------------
            PROJECT_ID = "proj-test-002"
            builder = evidence.EvidencePackBuilder()
            evidences = builder.build(
                cards=cards,
                task_type="tender",
                project_id=PROJECT_ID,
            )
            assert len(evidences) == len(cards)
            for ev in evidences:
                assert ev["evidence_type"] == "report"

            # ------------------------------------------------------------------
            # Create a product card (without report_meta) for capability matching
            # ------------------------------------------------------------------
            product_card = {
                "id": "card-product-001",
                "doc_file": "AMS1000_datasheet.md",
                "source_type": "markdown",
                "title": "AMS1000 安全特性",
                "level": 0,
                "path": "AMS1000_datasheet.md > 安全特性",
                "line_start": 0,
                "char_count": 80,
                "body": "AMS1000终端支持SM2/SM3/SM4国密算法",
                "tags": ["SM2", "SM3", "SM4", "国密"],
                "keywords": ["SM2", "SM3", "SM4", "AMS1000", "国密"],
                "models": ["AMS1000"],
                "related_topics": ["安全"],
                "aliases": [],
                "sibling_sections": [],
                "source_weight": 2,
                "report_meta": None,
                "semantic": _make_semantic(
                    intent_tags=["capability_query"],
                    quality_tier="high",
                    summary="AMS1000 SM2/SM3/SM4 support",
                ),
            }
            card_store.save(product_card)

            # ------------------------------------------------------------------
            # Tender matching
            # ------------------------------------------------------------------
            tender_svc = tender_mod.TenderService(conn)

            requirement = {
                "id": "req-001",
                "raw_text": "要求提供CMA检测报告，支持SM2/SM3/SM4国密算法",
                "requirement_type": "security",
                "target_models": ["AMS1000"],
                "required_capabilities": ["SM2", "SM3", "SM4"],
                "required_evidence": ["CMA"],
            }

            report_evidence = [c for c in cards if c.get("report_meta")]
            product_evidence = [product_card]

            match_result = tender_svc.match_single(
                requirement=requirement,
                product_evidence=product_evidence,
                report_evidence=report_evidence,
            )
            assert match_result["requirement_id"] == "req-001"
            assert match_result["judgement"] in ("satisfied", "partial", "unknown"), (
                f"Unexpected judgement: {match_result['judgement']}"
            )
            assert match_result["confidence"] > 0

        finally:
            db.models.get_db = original_get_db
            db.models.DB_PATH = original_db_path
            conn.close()
