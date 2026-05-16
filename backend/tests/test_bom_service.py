import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import sqlite3
import tempfile

from db.models import init_db
from services.bom_service import BomService


def _make_conn():
    """Create a temporary SQLite connection with full schema."""
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    conn = sqlite3.connect(tmp.name)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def test_bom_generate_from_evidence():
    """Generates BOM lines from evidence cards with prices and models."""
    conn = _make_conn()
    # Seed a project so FK constraint is satisfied
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO presales_projects (id, customer_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("proj1", "TestCustomer", now, now),
    )
    conn.commit()

    svc = BomService(conn)

    evidences = [
        {
            'id': 'card-1',
            'title': '视频终端 AE800',
            'body': '型号AE800，价格：15000，支持4K超高清。',
        },
        {
            'id': 'card-2',
            'title': 'MCU多点控制器 MX500',
            'body': '型号MX500，价格：85000，支持H.323/SIP双协议。',
        },
    ]

    result = svc.generate(
        project_id='proj1',
        scenario='会议室部署',
        room_count=5,
        deployment_type='on-prem',
        required_models=['AE800', 'MX500'],
        budget_limit=1000000,
        evidences=evidences,
    )

    assert 'output_id' in result
    assert len(result['lines']) == 2

    # Verify first line
    line0 = result['lines'][0]
    assert line0['model'] == 'AE800'
    assert line0['unit_price'] == 15000.0
    assert line0['quantity'] == 5
    assert line0['total_price'] == 75000.0

    # Verify second line
    line1 = result['lines'][1]
    assert line1['model'] == 'MX500'
    assert line1['unit_price'] == 85000.0
    assert line1['total_price'] == 425000.0

    # Total
    assert result['total_price'] == 500000.0

    # No risk flags
    assert result['risk_summary'] == []

    conn.close()


def test_bom_detects_discontinued():
    """Detects discontinued keywords and flags budget overrun."""
    conn = _make_conn()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO presales_projects (id, customer_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        ("proj2", "TestCustomer2", now, now),
    )
    conn.commit()

    svc = BomService(conn)

    evidences = [
        {
            'id': 'card-10',
            'title': '旧款终端 OL100',
            'body': '型号OL100，价格：20000，已停产，替代型号为NL200。',
        },
        {
            'id': 'card-11',
            'title': '新型终端 NL200',
            'body': '型号NL200，价格：25000。',
        },
    ]

    result = svc.generate(
        project_id='proj2',
        scenario='替换部署',
        room_count=10,
        deployment_type='on-prem',
        required_models=['OL100', 'NL200', 'MISSING999'],
        budget_limit=100000,
        evidences=evidences,
    )

    assert len(result['lines']) == 2
    assert result['total_price'] == 450000.0  # (20000+25000)*10

    risks = result['risk_summary']

    # Discontinued detected
    assert any('停产' in r or '停售' in r for r in risks)

    # Missing model detected
    assert any('MISSING999' in r for r in risks)

    # Budget exceeded detected
    assert any('预算超限' in r for r in risks)

    conn.close()


if __name__ == '__main__':
    test_bom_generate_from_evidence()
    test_bom_detects_discontinued()
    print('ALL 2 TESTS PASSED')
