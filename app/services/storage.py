import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import DB_PATH, get_default_api_key

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table for settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Table for analyses history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            created_at TEXT NOT NULL,
            model_used TEXT NOT NULL,
            total_mentions INTEGER NOT NULL,
            sentiment_summary TEXT NOT NULL,
            metrics_json TEXT NOT NULL,
            report_markdown TEXT NOT NULL,
            mentions_sample_json TEXT NOT NULL
        )
    """)
    
    # Initialize default settings if not exists
    cursor.execute("SELECT value FROM settings WHERE key = 'openrouter_api_key'")
    row = cursor.fetchone()
    if not row:
        default_key = get_default_api_key()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("openrouter_api_key", default_key))
    
    cursor.execute("SELECT value FROM settings WHERE key = 'selected_model'")
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("selected_model", "google/gemini-3.5-flash-lite"))

    cursor.execute("SELECT value FROM settings WHERE key = 'mcp_settings'")
    row = cursor.fetchone()
    if not row:
        default_mcp = {
            "enable_reddit": True,
            "enable_news": True,
            "enable_social_web": True,
            "apify_api_token": "",
            "brightdata_api_token": "",
            "exa_api_key": ""
        }
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("mcp_settings", json.dumps(default_mcp)))
        
    conn.commit()
    conn.close()

def get_setting(key: str, default: str = "") -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] is not None else default

def set_setting(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_all_settings() -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    
    settings = {}
    for k, v in rows:
        if k == "mcp_settings":
            try:
                settings[k] = json.loads(v)
            except Exception:
                settings[k] = {}
        else:
            settings[k] = v
            
    # Ensure defaults
    if "openrouter_api_key" not in settings or not settings["openrouter_api_key"]:
        settings["openrouter_api_key"] = get_default_api_key()
    if "selected_model" not in settings:
        settings["selected_model"] = "google/gemini-3.5-flash-lite"
    if "mcp_settings" not in settings:
        settings["mcp_settings"] = {
            "enable_reddit": True,
            "enable_news": True,
            "enable_social_web": True,
            "apify_api_token": "",
            "brightdata_api_token": "",
            "exa_api_key": ""
        }
    return settings

def save_analysis(
    analysis_id: str,
    topic: str,
    model_used: str,
    total_mentions: int,
    sentiment_summary: str,
    metrics: Dict[str, Any],
    report_markdown: str,
    mentions_sample: List[Dict[str, Any]]
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT OR REPLACE INTO analyses 
        (id, topic, created_at, model_used, total_mentions, sentiment_summary, metrics_json, report_markdown, mentions_sample_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        analysis_id,
        topic,
        now_str,
        model_used,
        total_mentions,
        sentiment_summary,
        json.dumps(metrics, ensure_ascii=False),
        report_markdown,
        json.dumps(mentions_sample, ensure_ascii=False)
    ))
    conn.commit()
    conn.close()

def get_history(limit: int = 30) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, topic, created_at, model_used, total_mentions, sentiment_summary, metrics_json
        FROM analyses
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r in rows:
        try:
            metrics = json.loads(r[6])
        except Exception:
            metrics = {}
            
        history.append({
            "id": r[0],
            "topic": r[1],
            "created_at": r[2],
            "model_used": r[3],
            "total_mentions": r[4],
            "sentiment_summary": r[5],
            "metrics": metrics
        })
    return history

def get_analysis_by_id(analysis_id: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, topic, created_at, model_used, total_mentions, sentiment_summary, metrics_json, report_markdown, mentions_sample_json
        FROM analyses
        WHERE id = ?
    """, (analysis_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    try:
        metrics = json.loads(row[6])
    except Exception:
        metrics = {}
    try:
        mentions = json.loads(row[8])
    except Exception:
        mentions = []
        
    return {
        "id": row[0],
        "topic": row[1],
        "created_at": row[2],
        "model_used": row[3],
        "total_mentions": row[4],
        "sentiment_summary": row[5],
        "metrics": metrics,
        "report_markdown": row[7],
        "mentions_sample": mentions
    }

def delete_analysis(analysis_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    conn.commit()
    conn.close()
