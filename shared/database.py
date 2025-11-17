"""
Database operations for SpeakSense
SQLite database management for FAQ storage
"""
import sqlite3
import json
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path
import uuid

from .config_loader import config
from .models import FAQEntry


class Database:
    """SQLite database manager for FAQ storage"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = config.get('database.path', './data/faq.db')

        # Convert to absolute path relative to project root
        if not Path(db_path).is_absolute():
            project_root = Path(__file__).parent.parent
            db_path = project_root / db_path

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = str(db_path)
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create FAQ table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faq (
                answer_id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                alternative_questions TEXT,  -- JSON array
                language TEXT DEFAULT 'auto',
                category TEXT DEFAULT 'general',
                audio_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create index for faster search
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_question ON faq(question)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category ON faq(category)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_language ON faq(language)
        ''')

        conn.commit()
        conn.close()

    def create_faq(
        self,
        question: str,
        answer: str,
        alternative_questions: List[str],
        language: str,
        category: str,
        audio_path: str
    ) -> FAQEntry:
        """Create a new FAQ entry"""
        conn = self.get_connection()
        cursor = conn.cursor()

        answer_id = str(uuid.uuid4())
        created_at = datetime.now()
        updated_at = created_at

        cursor.execute('''
            INSERT INTO faq (
                answer_id, question, answer, alternative_questions,
                language, category, audio_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            answer_id,
            question,
            answer,
            json.dumps(alternative_questions, ensure_ascii=False),
            language,
            category,
            audio_path,
            created_at,
            updated_at
        ))

        conn.commit()
        conn.close()

        return FAQEntry(
            answer_id=answer_id,
            question=question,
            answer=answer,
            alternative_questions=alternative_questions,
            language=language,
            category=category,
            audio_path=audio_path,
            created_at=created_at,
            updated_at=updated_at
        )

    def get_faq_by_id(self, answer_id: str) -> Optional[FAQEntry]:
        """Get FAQ by answer_id"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM faq WHERE answer_id = ?', (answer_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_faq_entry(row)
        return None

    def get_all_faqs(self) -> List[FAQEntry]:
        """Get all FAQ entries"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM faq ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_faq_entry(row) for row in rows]

    def update_faq(self, answer_id: str, updates: Dict) -> Optional[FAQEntry]:
        """Update FAQ entry"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        update_fields = []
        values = []

        if 'question' in updates:
            update_fields.append('question = ?')
            values.append(updates['question'])

        if 'answer' in updates:
            update_fields.append('answer = ?')
            values.append(updates['answer'])

        if 'alternative_questions' in updates:
            update_fields.append('alternative_questions = ?')
            values.append(json.dumps(updates['alternative_questions'], ensure_ascii=False))

        if 'language' in updates:
            update_fields.append('language = ?')
            values.append(updates['language'])

        if 'category' in updates:
            update_fields.append('category = ?')
            values.append(updates['category'])

        if 'audio_path' in updates:
            update_fields.append('audio_path = ?')
            values.append(updates['audio_path'])

        update_fields.append('updated_at = ?')
        values.append(datetime.now())

        values.append(answer_id)

        query = f"UPDATE faq SET {', '.join(update_fields)} WHERE answer_id = ?"
        cursor.execute(query, values)

        conn.commit()
        conn.close()

        return self.get_faq_by_id(answer_id)

    def delete_faq(self, answer_id: str) -> bool:
        """Delete FAQ entry"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM faq WHERE answer_id = ?', (answer_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    def search_faqs_by_keyword(self, keyword: str) -> List[FAQEntry]:
        """Simple keyword search in questions and answers"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM faq
            WHERE question LIKE ? OR answer LIKE ? OR alternative_questions LIKE ?
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_faq_entry(row) for row in rows]

    def _row_to_faq_entry(self, row) -> FAQEntry:
        """Convert database row to FAQEntry object"""
        return FAQEntry(
            answer_id=row['answer_id'],
            question=row['question'],
            answer=row['answer'],
            alternative_questions=json.loads(row['alternative_questions']) if row['alternative_questions'] else [],
            language=row['language'],
            category=row['category'],
            audio_path=row['audio_path'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )


# Global database instance
db = Database()
