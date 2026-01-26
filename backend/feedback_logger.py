import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'feedback.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_question TEXT,
            ai_answer TEXT,
            rating TEXT,
            expected_answer TEXT,
            model_used TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_feedback(question, answer, rating, expected_answer=None, model="gemini-2.5-pro"):
    init_db() # Ensure table exists
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO feedback (timestamp, user_question, ai_answer, rating, expected_answer, model_used)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (datetime.now().isoformat(), question, answer, rating, expected_answer, model))
    conn.commit()
    conn.close()
    print(f"  [Feedback Logged] Rating: {rating}")
