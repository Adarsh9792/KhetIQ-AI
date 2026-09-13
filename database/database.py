import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "khetiq.db")

def get_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database table for storing consultation history."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            language TEXT NOT NULL,
            crop TEXT NOT NULL,
            village TEXT,
            district TEXT,
            state TEXT,
            crop_age TEXT,
            question TEXT NOT NULL,
            has_image INTEGER DEFAULT 0,
            response_json TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_consultation(
    language: str,
    crop: str,
    village: str,
    district: str,
    state: str,
    crop_age: str,
    question: str,
    has_image: bool,
    response_data: Dict[str, Any]
) -> int:
    """
    Saves a farmer consultation record to SQLite.
    Returns the newly generated consultation ID.
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response_json = json.dumps(response_data, ensure_ascii=False)
    
    cursor.execute("""
        INSERT INTO consultations (
            timestamp, language, crop, village, district, state, crop_age, question, has_image, response_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now_str,
        language,
        crop,
        village or "",
        district or "",
        state or "",
        crop_age or "",
        question,
        1 if has_image else 0,
        response_json
    ))
    
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def get_recent_consultations(limit: int = 20) -> List[Dict[str, Any]]:
    """Fetches recent consultations sorted by newest first."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM consultations ORDER BY id DESC LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    results = []
    for row in rows:
        item = dict(row)
        try:
            item["response_data"] = json.loads(item["response_json"])
        except Exception:
            item["response_data"] = {}
        results.append(item)
        
    conn.close()
    return results

def clear_history() -> bool:
    """Clears all historical consultations from the database."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM consultations")
    conn.commit()
    conn.close()
    return True
