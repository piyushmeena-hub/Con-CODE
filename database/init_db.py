import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "concode.db")

def init_database():
    print(f"Initializing database at {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create frontend table (Student Self-Tracking)
    c.execute("""
        CREATE TABLE IF NOT EXISTS subject_attendance (
            subject TEXT PRIMARY KEY,
            attended INTEGER,
            total INTEGER
        )
    """)
    
    # Create backend table (Quick Attendance Logger)
    c.execute("""
        CREATE TABLE IF NOT EXISTS student_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
