import os
import time
from db.models import get_db


def check_health() -> dict:
    """Comprehensive health check."""
    checks = {}
    start = time.time()

    try:
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'

    try:
        conn = get_db()
        pending = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='pending'").fetchone()['c']
        running = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='running'").fetchone()['c']
        failed = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='failed'").fetchone()['c']
        conn.close()
        checks['jobs_pending'] = pending
        checks['jobs_running'] = running
        checks['jobs_failed'] = failed
    except Exception:
        pass

    try:
        data_dir = os.environ.get('KB_DATA_DIR', './data')
        cards_dir = os.path.join(data_dir, 'cards', 'sections')
        if os.path.isdir(cards_dir):
            count = len([f for f in os.listdir(cards_dir) if f.endswith('.json')])
            checks['cards_count'] = count
    except Exception:
        pass

    try:
        conn = get_db()
        evidence_count = conn.execute("SELECT COUNT(*) as c FROM evidence_packs WHERE archived_at IS NULL").fetchone()['c']
        report_count = conn.execute("SELECT COUNT(*) as c FROM evidence_packs WHERE evidence_type='report' AND archived_at IS NULL").fetchone()['c']
        conn.close()
        checks['evidence_count'] = evidence_count
        checks['report_evidence_count'] = report_count
    except Exception:
        pass

    elapsed = int((time.time() - start) * 1000)

    return {
        'status': 'healthy',
        'version': '7.5',
        'checks': checks,
        'latency_ms': elapsed,
    }
