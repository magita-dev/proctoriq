import sqlite3
import json
import os
import logging

DB_FILE = "system_siege.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite tables for candidates, attempts, telemetry, QAs, and appeals."""
    logging.info("Initializing SQLite database connection and schemas...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Candidates Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    
    # 2. Attempts Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id TEXT NOT NULL,
            code TEXT NOT NULL,
            reference_code TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            status TEXT NOT NULL,
            similarity_score REAL NOT NULL,
            velocity_score INTEGER NOT NULL,
            velocity_rating TEXT NOT NULL,
            style_score INTEGER NOT NULL,
            style_rating TEXT NOT NULL,
            interview_score INTEGER NOT NULL,
            interview_verdict TEXT NOT NULL,
            trust_graph_json TEXT NOT NULL,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id)
        )
    """)
    
    # 3. Telemetry Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            length INTEGER NOT NULL,
            char TEXT,
            content TEXT,
            FOREIGN KEY (attempt_id) REFERENCES attempts(id)
        )
    """)
    
    # 4. Interview Answers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            FOREIGN KEY (attempt_id) REFERENCES attempts(id)
        )
    """)
    
    # 5. Appeals Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appeals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER UNIQUE NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            reviewer_note TEXT,
            FOREIGN KEY (attempt_id) REFERENCES attempts(id)
        )
    """)
    
    conn.commit()
    conn.close()
    logging.info("Database schemas created successfully.")

# --- CREATE HELPERS ---

def save_candidate(cand_id: str, name: str, role: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO candidates (id, name, role) VALUES (?, ?, ?)",
        (cand_id, name, role)
    )
    conn.commit()
    conn.close()

def save_attempt(candidate_id: str, code: str, reference_code: str, 
                 similarity: float, velocity: dict, style: dict, 
                 interview: dict, graph: dict) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Extract sub-scores
    v_score = velocity.get("risk_score", 0)
    v_rating = velocity.get("rating", "")
    s_score = style.get("risk_score", 0)
    s_rating = style.get("rating", "")
    i_score = 100 - interview.get("consistency_score", 100)
    i_verdict = interview.get("verdict", "")
    
    overall_risk = graph.get("overall_risk", 0)
    status = graph.get("status", "safe")
    
    cursor.execute("""
        INSERT INTO attempts (
            candidate_id, code, reference_code, risk_score, status, 
            similarity_score, velocity_score, velocity_rating, 
            style_score, style_rating, interview_score, interview_verdict, 
            trust_graph_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        candidate_id, code, reference_code, overall_risk, status,
        similarity, v_score, v_rating, s_score, s_rating,
        i_score, i_verdict, json.dumps(graph)
    ))
    
    attempt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return attempt_id

def save_telemetry(attempt_id: int, events: list):
    conn = get_db_connection()
    cursor = conn.cursor()
    for ev in events:
        cursor.execute("""
            INSERT INTO telemetry (attempt_id, event_type, timestamp, length, char, content)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            attempt_id, ev.get("type"), ev.get("timestamp"), ev.get("length"),
            ev.get("char"), ev.get("content")
        ))
    conn.commit()
    conn.close()

def save_qa(attempt_id: int, qa_responses: list):
    conn = get_db_connection()
    cursor = conn.cursor()
    for qa in qa_responses:
        cursor.execute("""
            INSERT INTO interview_answers (attempt_id, question, answer)
            VALUES (?, ?, ?)
        """, (attempt_id, qa.get("q"), qa.get("a")))
    conn.commit()
    conn.close()

def create_appeal(attempt_id: int, reason: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO appeals (attempt_id, reason, status, reviewer_note)
        VALUES (?, ?, 'pending', '')
    """, (attempt_id, reason))
    
    # Update attempt status to warning
    cursor.execute("""
        UPDATE attempts SET status = 'warning' WHERE id = ?
    """, (attempt_id,))
    
    conn.commit()
    conn.close()

def resolve_appeal(attempt_id: int, status_choice: str, note: str):
    """Updates appeal status and updates parent attempt risk profile accordingly."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Save appeal state
    cursor.execute("""
        UPDATE appeals 
        SET status = ?, reviewer_note = ?
        WHERE attempt_id = ?
    """, (status_choice, note, attempt_id))
    
    if status_choice == "resolved":
        # Reset risk elements
        cursor.execute("SELECT trust_graph_json FROM attempts WHERE id = ?", (attempt_id,))
        row = cursor.fetchone()
        if row:
            graph = json.loads(row["trust_graph_json"])
            # Clear final node and set overall risk to safe minimum
            graph["overall_risk"] = 15
            graph["status"] = "safe"
            if len(graph["nodes"]) > 0:
                graph["nodes"][-1]["type"] = "safe"
                graph["nodes"][-1]["risk"] = 15
                graph["nodes"][-1]["desc"] = f"Flags cleared: {note}"
                
            cursor.execute("""
                UPDATE attempts 
                SET risk_score = 15, status = 'safe', trust_graph_json = ?
                WHERE id = ?
            """, (json.dumps(graph), attempt_id))
            
    elif status_choice == "rejected":
        # Keep high risk
        cursor.execute("""
            UPDATE attempts 
            SET status = 'danger'
            WHERE id = ?
        """, (attempt_id,))
        
    conn.commit()
    conn.close()

# --- READ HELPERS ---

def get_candidate_attempts(candidate_id: str) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM attempts WHERE candidate_id = ? ORDER BY id DESC
    """, (candidate_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_attempt_detail(attempt_id: int) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Attempt core
    cursor.execute("SELECT * FROM attempts WHERE id = ?", (attempt_id,))
    attempt_row = cursor.fetchone()
    if not attempt_row:
        conn.close()
        return {}
        
    attempt = dict(attempt_row)
    attempt["trust_graph"] = json.loads(attempt["trust_graph_json"])
    
    # Telemetry
    cursor.execute("SELECT * FROM telemetry WHERE attempt_id = ?", (attempt_id,))
    attempt["telemetry"] = [dict(r) for r in cursor.fetchall()]
    
    # QAs
    cursor.execute("SELECT * FROM interview_answers WHERE attempt_id = ?", (attempt_id,))
    attempt["qa_responses"] = [dict(r) for r in cursor.fetchall()]
    
    # Appeal
    cursor.execute("SELECT * FROM appeals WHERE attempt_id = ?", (attempt_id,))
    appeal_row = cursor.fetchone()
    attempt["appeal"] = dict(appeal_row) if appeal_row else None
    
    conn.close()
    return attempt
