import sqlite3
import os
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_database()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_database(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    category TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ai_result TEXT
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_file_path ON processed_files(file_path)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_file_hash ON processed_files(file_hash)
            ''')
            conn.commit()

    @staticmethod
    def _compute_file_hash(file_path: str) -> str:
        hash_obj = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return ""

    def is_file_processed(self, file_path: str) -> bool:
        file_hash = self._compute_file_hash(file_path)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM processed_files 
                WHERE file_path = ? OR file_hash = ?
            ''', (file_path, file_hash))
            return cursor.fetchone() is not None

    def add_processed_file(
        self, 
        file_path: str, 
        category: str, 
        ai_result: str = ""
    ) -> None:
        file_hash = self._compute_file_hash(file_path)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO processed_files 
                (file_path, file_hash, category, ai_result, processed_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (file_path, file_hash, category, ai_result, datetime.now()))
            conn.commit()

    def get_unprocessed_files(self, file_paths: List[str]) -> List[str]:
        if not file_paths:
            return []
        
        placeholders = ', '.join(['?'] * len(file_paths))
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT file_path FROM processed_files 
                WHERE file_path IN ({placeholders})
            ''', file_paths)
            processed = {row[0] for row in cursor.fetchall()}
        
        return [fp for fp in file_paths if fp not in processed]

    def get_all_processed_files(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM processed_files ORDER BY processed_at DESC')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_all(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM processed_files')
            conn.commit()

    def clear_invalid_records(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, file_path FROM processed_files')
            records = cursor.fetchall()
            
            invalid_ids = []
            for record_id, file_path in records:
                if not os.path.exists(file_path):
                    invalid_ids.append(record_id)
            
            if invalid_ids:
                placeholders = ', '.join(['?'] * len(invalid_ids))
                cursor.execute(f'DELETE FROM processed_files WHERE id IN ({placeholders})', invalid_ids)
                conn.commit()
            
            return len(invalid_ids)
