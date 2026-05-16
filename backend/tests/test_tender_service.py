import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import tempfile
from datetime import datetime, timezone, timedelta

from services.tender_service import TenderService


def _make_conn():
    """Create a temporary SQLite connection for testing."""
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    conn = sqlite3.connect(tmp.name)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id TEXT PRIMARY KEY,
            data TEXT
        )
    """)
    conn.commit()
    return conn


def test_extract_requirements_from_text():
    """Extracts requirements from multi-line tender text."""
    conn = _make_conn()
    svc = TenderService(conn)

    tender_text = """
    1. 视频终端须支持国密SM2加密算法，具备SM3完整性校验能力。
    2. 终端须支持H.323和SIP双协议栈，兼容现有MCU设备。
    3. 供应商须提供CMA认可的第三方检测报告（型号AE800）。
    4. 项目预算不超过人民币150万元。
    """

    requirements = svc.extract_requirements(tender_text)

    assert len(requirements) == 4

    # First requirement: security type with SM2/SM3 capabilities
    r0 = requirements[0]
    assert 'SM2' in r0['required_capabilities']
    assert 'SM3' in r0['required_capabilities']
    assert r0['requirement_type'] == 'security'

    # Second requirement: compatibility type with H.323/SIP
    r1 = requirements[1]
    assert 'H.323' in r1['required_capabilities']
    assert 'SIP' in r1['required_capabilities']
    assert r1['requirement_type'] == 'compatibility'

    # Third requirement: has evidence requirement and model
    r2 = requirements[2]
    assert 'CMA' in r2['required_evidence']
    assert 'AE800' in r2['target_models']

    # Fourth requirement: price type
    r3 = requirements[3]
    assert r3['requirement_type'] == 'price'

    conn.close()


def test_match_requirements_to_evidence():
    """Matches with both product and report evidence -> satisfied."""
    conn = _make_conn()
    svc = TenderService(conn)

    future_date = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()

    requirement = {
        'id': 'req001',
        'raw_text': '支持SM2加密',
        'requirement_type': 'security',
        'target_models': [],
        'required_capabilities': ['SM2'],
        'required_evidence': [],
    }

    product_evidence = [
        {
            'tags': ['SM2', '国密'],
            'keywords': [],
            'related_topics': [],
            'title': 'SM2加密支持',
            'body': '本终端支持国密SM2算法',
        }
    ]

    report_evidence = [
        {
            'report_meta': {
                'valid_to': future_date,
                'scan_available': True,
            }
        }
    ]

    result = svc.match_single(requirement, product_evidence, report_evidence)

    assert result['requirement_id'] == 'req001'
    assert result['judgement'] == 'satisfied'
    assert result['confidence'] >= 0.75
    assert result['risks'] == []

    conn.close()


def test_match_partial_when_no_report():
    """Capability found but no report -> partial."""
    conn = _make_conn()
    svc = TenderService(conn)

    requirement = {
        'id': 'req002',
        'raw_text': '支持SIP协议',
        'requirement_type': 'compatibility',
        'target_models': [],
        'required_capabilities': ['SIP'],
        'required_evidence': [],
    }

    product_evidence = [
        {
            'tags': ['SIP'],
            'keywords': [],
            'related_topics': [],
            'title': 'SIP协议支持',
            'body': '支持SIP协议栈',
        }
    ]

    report_evidence = []

    result = svc.match_single(requirement, product_evidence, report_evidence)

    assert result['requirement_id'] == 'req002'
    assert result['judgement'] == 'partial'
    assert '检测报告未确认' in result['risks']

    conn.close()


def test_match_expired_report():
    """Expired report -> not satisfied with risk."""
    conn = _make_conn()
    svc = TenderService(conn)

    past_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()

    requirement = {
        'id': 'req003',
        'raw_text': '支持SM4加密',
        'requirement_type': 'security',
        'target_models': [],
        'required_capabilities': ['SM4'],
        'required_evidence': [],
    }

    product_evidence = [
        {
            'tags': ['SM4'],
            'keywords': [],
            'related_topics': [],
            'title': 'SM4加密支持',
            'body': '支持国密SM4算法',
        }
    ]

    report_evidence = [
        {
            'report_meta': {
                'valid_to': past_date,
                'scan_available': True,
            }
        }
    ]

    result = svc.match_single(requirement, product_evidence, report_evidence)

    assert result['requirement_id'] == 'req003'
    assert '报告已过期' in result['risks']
    # Expired report gives report_score=0, capability_score=1.0 -> partial
    assert result['judgement'] in ('partial', 'not_satisfied')

    conn.close()


if __name__ == '__main__':
    test_extract_requirements_from_text()
    test_match_requirements_to_evidence()
    test_match_partial_when_no_report()
    test_match_expired_report()
    print('ALL 4 TESTS PASSED')
