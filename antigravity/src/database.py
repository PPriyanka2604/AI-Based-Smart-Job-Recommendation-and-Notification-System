import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path='data/jobs_history.db'):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs_history (
                id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                description TEXT,
                url TEXT,
                match_score REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                parsed_content TEXT,
                last_search_query TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_job_to_history(self, job):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO jobs_history (id, title, company, description, url, match_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (job.get('id'), job.get('title'), job.get('company', {}).get('display_name'), 
                  job.get('description'), job.get('redirect_url'), job.get('match_score')))
            conn.commit()
        except Exception as e:
            print(f"Error adding to history: {e}")
        finally:
            conn.close()

    def is_duplicate(self, job_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM jobs_history WHERE id = ?', (job_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

if __name__ == "__main__":
    db = DatabaseManager()
    print("DatabaseManager initialized.")
