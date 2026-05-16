"""
数据库模型 - platform.db
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "platform.db"

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()
    
    # 文档管理
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS uploaded_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_name TEXT NOT NULL,
        stored_name TEXT NOT NULL UNIQUE,
        file_type TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        sha256 TEXT NOT NULL,
        storage_path TEXT NOT NULL,
        source_store_path TEXT,
        cards_count INTEGER DEFAULT 0,
        pipeline_status TEXT DEFAULT 'pending',
        pipeline_error TEXT,
        version_label TEXT,
        effective_from TEXT,
        effective_to TEXT,
        superseded_by INTEGER REFERENCES uploaded_files(id),
        is_current INTEGER DEFAULT 1,
        uploaded_at TEXT DEFAULT (datetime('now')),
        processed_at TEXT,
        updated_at TEXT DEFAULT (datetime('now'))
    )
    """)
    
    # Job 任务系统
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        target_id INTEGER,
        payload TEXT,
        progress_pct INTEGER DEFAULT 0,
        progress_detail TEXT,
        retry_count INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 3,
        last_error TEXT,
        idempotency_key TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        started_at TEXT,
        completed_at TEXT,
        triggered_by TEXT DEFAULT 'user',
        parent_job_id INTEGER REFERENCES jobs(id)
    )
    """)
    
    # 查询反馈
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS query_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_id TEXT NOT NULL,
        query_text TEXT NOT NULL,
        card_id TEXT NOT NULL,
        feedback TEXT NOT NULL,
        route_used TEXT,
        route_source TEXT,
        hit_rate REAL,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)
    
    # 路由学习
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS route_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_pattern TEXT NOT NULL,
        query_hash TEXT NOT NULL UNIQUE,
        expected_route TEXT NOT NULL,
        confidence REAL DEFAULT 0.5,
        positive_count INTEGER DEFAULT 0,
        negative_count INTEGER DEFAULT 0,
        total_count INTEGER DEFAULT 0,
        source TEXT DEFAULT 'rule',
        is_active INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )
    """)
    
    # 路由缓存
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS route_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_hash TEXT NOT NULL UNIQUE,
        query_text TEXT NOT NULL,
        source_type TEXT NOT NULL,
        models TEXT,
        hit_count INTEGER DEFAULT 1,
        last_hit_at TEXT DEFAULT (datetime('now')),
        created_at TEXT DEFAULT (datetime('now'))
    )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_uf_sha256 ON uploaded_files(sha256)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_uf_current ON uploaded_files(is_current, file_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_uf_status ON uploaded_files(pipeline_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_type_status ON jobs(job_type, status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qf_query ON query_feedback(query_text)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rm_active ON route_mappings(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rc_hash ON route_cache(query_hash)")
    
    conn.commit()
    conn.close()
