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

def init_db(conn):
    """初始化数据库"""
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

    # v7.5: Evidence packs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence_packs (
        id TEXT PRIMARY KEY,
        project_id TEXT,
        source_card_id TEXT NOT NULL,
        source_type TEXT NOT NULL CHECK(source_type IN ('excel','word','markdown','txt','ppt','report')),
        evidence_type TEXT NOT NULL,
        claim TEXT NOT NULL,
        body TEXT NOT NULL,
        source TEXT NOT NULL,
        confidence REAL NOT NULL DEFAULT 0,
        freshness TEXT NOT NULL DEFAULT 'unknown' CHECK(freshness IN ('current','expired','history','unknown')),
        risk_flags TEXT NOT NULL DEFAULT '[]',
        created_by_task_id TEXT,
        created_at TEXT NOT NULL,
        archived_at TEXT
    )
    """)

    # v7.5: Presales projects
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS presales_projects (
        id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        industry TEXT,
        stage TEXT NOT NULL DEFAULT 'draft',
        deployment_type TEXT,
        description TEXT,
        owner TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        archived_at TEXT
    )
    """)

    # v7.5: Project requirements
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_requirements (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        requirement_type TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        structured_json TEXT NOT NULL DEFAULT '{}',
        source_file_id TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(project_id) REFERENCES presales_projects(id)
    )
    """)

    # v7.5: Project outputs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_outputs (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        output_type TEXT NOT NULL CHECK(output_type IN ('proposal','tender','bom','reply')),
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','evidence_checked','human_reviewed','exported','archived')),
        content_md TEXT,
        content_json TEXT NOT NULL DEFAULT '{}',
        export_path TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        reviewed_by TEXT,
        reviewed_at TEXT,
        FOREIGN KEY(project_id) REFERENCES presales_projects(id)
    )
    """)

    # v7.5: Project evidence links
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_evidence_links (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        output_id TEXT NOT NULL,
        evidence_id TEXT NOT NULL,
        target_path TEXT NOT NULL,
        link_role TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(project_id) REFERENCES presales_projects(id),
        FOREIGN KEY(output_id) REFERENCES project_outputs(id),
        FOREIGN KEY(evidence_id) REFERENCES evidence_packs(id)
    )
    """)

    # v7.5: Project feedback
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_feedback (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        output_id TEXT,
        feedback_type TEXT NOT NULL CHECK(feedback_type IN ('accept','edit','reject','comment')),
        target_path TEXT,
        before_text TEXT,
        after_text TEXT,
        comment TEXT,
        created_by TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # v7.5: Templates
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS templates (
        id TEXT PRIMARY KEY,
        template_type TEXT NOT NULL CHECK(template_type IN ('proposal','tender','reply','ppt')),
        name TEXT NOT NULL,
        industry TEXT,
        deployment_type TEXT,
        file_path TEXT NOT NULL,
        schema_json TEXT NOT NULL DEFAULT '{}',
        enabled INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)

    # v7.5: Indexes for new tables
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_project ON evidence_packs(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_card ON evidence_packs(source_card_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence_packs(evidence_type)")

    conn.commit()
