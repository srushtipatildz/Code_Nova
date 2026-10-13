import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "mayi.db")

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DB_PATH):
    """Initializes the SQLite database with required tables for sessions and audit trail."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            status TEXT NOT NULL,  -- 'ACTIVE', 'STOPPED', 'EXPIRED'
            allowed_tools TEXT NOT NULL, -- JSON array
            blocked_tools TEXT NOT NULL  -- JSON array
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            tool_args TEXT NOT NULL,      -- JSON
            rationale TEXT NOT NULL,      -- Agent's justification
            status TEXT NOT NULL,         -- 'PROPOSED', 'APPROVED', 'DENIED_BY_USER', 'AUTO_BLOCKED_POLICY', 'AUTO_BLOCKED_EXPIRED', 'EXECUTED', 'FAILED'
            result TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        """)
        conn.commit()

def create_session(
    session_id: str,
    duration_minutes: int,
    allowed_tools: List[str],
    blocked_tools: List[str],
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """Creates a new session with an expiry window and scoped permissions."""
    now = datetime.now(timezone.utc)
    expires_at = now.timestamp() + (duration_minutes * 60)
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO sessions (session_id, created_at, expires_at, status, allowed_tools, blocked_tools)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            now.isoformat(),
            datetime.fromtimestamp(expires_at, timezone.utc).isoformat(),
            "ACTIVE",
            json.dumps(allowed_tools),
            json.dumps(blocked_tools)
        ))
        conn.commit()
    
    return {
        "session_id": session_id,
        "created_at": now.isoformat(),
        "expires_at": datetime.fromtimestamp(expires_at, timezone.utc).isoformat(),
        "status": "ACTIVE",
        "allowed_tools": allowed_tools,
        "blocked_tools": blocked_tools
    }

def get_session(session_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetches session metadata, evaluating if it has naturally expired."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        sess = dict(row)
        sess["allowed_tools"] = json.loads(sess["allowed_tools"])
        sess["blocked_tools"] = json.loads(sess["blocked_tools"])
        
        # Check automatic expiration
        if sess["status"] == "ACTIVE":
            exp_time = datetime.fromisoformat(sess["expires_at"]).timestamp()
            now_time = datetime.now(timezone.utc).timestamp()
            if now_time >= exp_time:
                cursor.execute("UPDATE sessions SET status = 'EXPIRED' WHERE session_id = ?", (session_id,))
                conn.commit()
                sess["status"] = "EXPIRED"
                
        return sess

def stop_session(session_id: str, db_path: str = DB_PATH) -> bool:
    """Instant kill switch: permanently terminates session."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET status = 'STOPPED' WHERE session_id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0

def log_action(
    session_id: str,
    tool_name: str,
    tool_args: Dict[str, Any],
    rationale: str,
    status: str,
    result: Optional[str] = None,
    db_path: str = DB_PATH
) -> int:
    """Logs an action proposal or direct block event to SQLite."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO actions (session_id, timestamp, tool_name, tool_args, rationale, status, result)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            now,
            tool_name,
            json.dumps(tool_args),
            rationale,
            status,
            result or ""
        ))
        conn.commit()
        return cursor.lastrowid

def update_action_status(
    action_id: int,
    status: str,
    result: Optional[str] = None,
    db_path: str = DB_PATH
) -> bool:
    """Updates the action status (e.g. APPROVED, DENIED, EXECUTED)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if result is not None:
            cursor.execute("""
            UPDATE actions SET status = ?, result = ? WHERE id = ?
            """, (status, result, action_id))
        else:
            cursor.execute("""
            UPDATE actions SET status = ? WHERE id = ?
            """, (status, action_id))
        conn.commit()
        return cursor.rowcount > 0

def get_actions(session_id: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Retrieves all logged actions for a session."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM actions WHERE session_id = ? ORDER BY id ASC", (session_id,))
        rows = cursor.fetchall()
        actions = []
        for r in rows:
            act = dict(r)
            try:
                act["tool_args"] = json.loads(act["tool_args"])
            except Exception:
                pass
            actions.append(act)
        return actions

def export_receipt_json(session_id: str, db_path: str = DB_PATH) -> str:
    """Generates an itemized JSON audit receipt for the session."""
    session = get_session(session_id, db_path)
    actions = get_actions(session_id, db_path)
    receipt = {
        "title": "MayI Audit Receipt",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "session": session,
        "actions_summary": {
            "total_actions": len(actions),
            "executed": sum(1 for a in actions if a["status"] == "EXECUTED"),
            "denied_by_user": sum(1 for a in actions if a["status"] == "DENIED_BY_USER"),
            "auto_blocked_policy": sum(1 for a in actions if a["status"] == "AUTO_BLOCKED_POLICY"),
            "auto_blocked_expired": sum(1 for a in actions if a["status"] == "AUTO_BLOCKED_EXPIRED"),
        },
        "itemized_log": actions
    }
    return json.dumps(receipt, indent=2)

def export_receipt_markdown(session_id: str, db_path: str = DB_PATH) -> str:
    """Generates a human-readable Markdown audit receipt."""
    session = get_session(session_id, db_path)
    actions = get_actions(session_id, db_path)
    
    if not session:
        return "# Receipt not found"
    
    md = []
    md.append(f"# 🧾 MayI Agent Audit Receipt")
    md.append(f"**Session ID:** `{session['session_id']}`")
    md.append(f"**Status:** `{session['status']}`")
    md.append(f"**Created At:** {session['created_at']}")
    md.append(f"**Expires At:** {session['expires_at']}\n")
    
    md.append("### 🔐 Policy Scope")
    md.append(f"- **Allowed Tools:** `{', '.join(session['allowed_tools']) or 'None'}`")
    md.append(f"- **Blocked Tools:** `{', '.join(session['blocked_tools']) or 'None'}`\n")
    
    md.append("### 📊 Summary")
    executed = sum(1 for a in actions if a['status'] == 'EXECUTED')
    denied = sum(1 for a in actions if a['status'] == 'DENIED_BY_USER')
    blocked = sum(1 for a in actions if a['status'] in ('AUTO_BLOCKED_POLICY', 'AUTO_BLOCKED_EXPIRED'))
    md.append(f"- **Total Actions Proposed:** {len(actions)}")
    md.append(f"- **Executed:** {executed}")
    md.append(f"- **Denied by User:** {denied}")
    md.append(f"- **Blocked by Policy/Expiry:** {blocked}\n")
    
    md.append("### 📜 Itemized Activity Trail")
    if not actions:
        md.append("_No actions were recorded in this session._")
    else:
        for idx, act in enumerate(actions, 1):
            badge = "🟢" if act['status'] == "EXECUTED" else "🛑" if "BLOCK" in act['status'] else "❌" if "DENIED" in act['status'] else "⏳"
            md.append(f"#### {idx}. {badge} {act['tool_name']} `[{act['status']}]`")
            md.append(f"- **Time:** {act['timestamp']}")
            md.append(f"- **Agent's Rationale:** _{act['rationale']}_")
            md.append(f"- **Arguments:** `{json.dumps(act['tool_args'])}`")
            if act['result']:
                md.append(f"- **Result:** {act['result']}")
            md.append("")
            
    md.append("\n---\n*Verified by MayI Consent Engine • Inspired by the idea of agent consent layers, such as My Agent Ohana.*")
    return "\n".join(md)
