"""
Episodic Memory
Uses SQLite to store research session history
"""

import os
import json
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime


DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "episodic.db"
)


def _get_connection():
    """Get SQLite connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    """Initialize database tables if they don't exist"""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            query TEXT NOT NULL,
            query_type TEXT,
            companies TEXT,
            plan TEXT,
            tools_used TEXT,
            tools_failed TEXT,
            fallbacks_triggered TEXT,
            outcome TEXT,
            evaluation_score REAL,
            total_tool_calls INTEGER,
            memory_hits INTEGER,
            duration_seconds REAL,
            report_length INTEGER,
            timestamp TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_name TEXT NOT NULL,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            avg_response_time REAL DEFAULT 0,
            last_used TEXT,
            last_error TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_session(session_data: Dict[str, Any]) -> bool:
    """
    Save a completed research session to episodic memory.

    Args:
        session_data: Dictionary with session details

    Returns:
        True if saved successfully
    """

    _init_db()

    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO research_sessions (
                session_id, query, query_type, companies, plan,
                tools_used, tools_failed, fallbacks_triggered,
                outcome, evaluation_score, total_tool_calls,
                memory_hits, duration_seconds, report_length, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_data.get("session_id", "unknown"),
            session_data.get("query", ""),
            session_data.get("query_type", ""),
            json.dumps(session_data.get("companies", [])),
            json.dumps(session_data.get("plan", [])),
            json.dumps(session_data.get("tools_used", [])),
            json.dumps(session_data.get("tools_failed", [])),
            json.dumps(session_data.get("fallbacks_triggered", [])),
            session_data.get("outcome", "completed"),
            session_data.get("evaluation_score", 0.0),
            session_data.get("total_tool_calls", 0),
            session_data.get("memory_hits", 0),
            session_data.get("duration_seconds", 0.0),
            session_data.get("report_length", 0),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        print(f"[Episodic] Session saved: {session_data.get('session_id', 'unknown')}")
        return True

    except Exception as e:
        print(f"[Episodic] Save error: {e}")
        return False


def get_previous_research(
    ticker: str = None,
    query_type: str = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve previous research sessions.

    Args:
        ticker: Filter by company ticker
        query_type: Filter by query type
        limit: Maximum number of sessions to return

    Returns:
        List of previous research sessions
    """

    _init_db()

    try:
        conn = _get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM research_sessions"
        params = []
        conditions = []

        if ticker:
            conditions.append("companies LIKE ?")
            params.append(f"%{ticker}%")

        if query_type:
            conditions.append("query_type = ?")
            params.append(query_type)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            sessions.append({
                "session_id": row["session_id"],
                "query": row["query"],
                "query_type": row["query_type"],
                "companies": json.loads(row["companies"] or "[]"),
                "outcome": row["outcome"],
                "evaluation_score": row["evaluation_score"],
                "total_tool_calls": row["total_tool_calls"],
                "timestamp": row["timestamp"]
            })

        return sessions

    except Exception as e:
        print(f"[Episodic] Retrieve error: {e}")
        return []


def get_episodic_stats() -> Dict[str, Any]:
    """Get statistics from episodic memory"""

    _init_db()

    try:
        conn = _get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM research_sessions")
        total = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT AVG(evaluation_score) as avg_score,
                   AVG(total_tool_calls) as avg_calls,
                   AVG(duration_seconds) as avg_duration
            FROM research_sessions
        """)
        stats = cursor.fetchone()
        conn.close()

        return {
            "total_sessions": total,
            "avg_evaluation_score": round(stats["avg_score"] or 0, 2),
            "avg_tool_calls": round(stats["avg_calls"] or 0, 1),
            "avg_duration_seconds": round(stats["avg_duration"] or 0, 1)
        }

    except Exception as e:
        return {"error": str(e), "total_sessions": 0}