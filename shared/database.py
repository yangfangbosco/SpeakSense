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
from .models import FAQEntry, IntentEntry


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
                audio_status TEXT DEFAULT 'pending',  -- pending, generating, completed, failed
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Migrate existing database: add audio_status column if it doesn't exist
        try:
            cursor.execute("SELECT audio_status FROM faq LIMIT 1")
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            cursor.execute("ALTER TABLE faq ADD COLUMN audio_status TEXT DEFAULT 'pending'")
            # Update existing FAQs with audio_path to 'completed'
            cursor.execute("UPDATE faq SET audio_status = 'completed' WHERE audio_path IS NOT NULL AND audio_path != ''")
            conn.commit()

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

        # Create Intent table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS intent (
                intent_id TEXT PRIMARY KEY,
                intent_name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                trigger_phrases TEXT NOT NULL,  -- JSON array
                action_type TEXT NOT NULL,
                action_config TEXT NOT NULL,  -- JSON object
                language TEXT DEFAULT 'auto',
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create index for faster intent search
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_intent_name ON intent(intent_name)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_intent_category ON intent(category)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_intent_language ON intent(language)
        ''')

        # Create Query Logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_logs (
                log_id TEXT PRIMARY KEY,
                query_text TEXT NOT NULL,
                matched_type TEXT,
                matched_id TEXT,
                matched_question TEXT,
                confidence REAL,
                response_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create index for faster query log search
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_query_created_at ON query_logs(created_at)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_query_matched_type ON query_logs(matched_type)
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
        audio_path: str,
        audio_status: str = "pending"
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
                language, category, audio_path, audio_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            answer_id,
            question,
            answer,
            json.dumps(alternative_questions, ensure_ascii=False),
            language,
            category,
            audio_path,
            audio_status,
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
            audio_status=audio_status,
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

        if 'audio_status' in updates:
            update_fields.append('audio_status = ?')
            values.append(updates['audio_status'])

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
        # Handle audio_status which may not exist in old databases
        try:
            audio_status = row['audio_status']
        except (KeyError, IndexError):
            audio_status = 'pending'

        return FAQEntry(
            answer_id=row['answer_id'],
            question=row['question'],
            answer=row['answer'],
            alternative_questions=json.loads(row['alternative_questions']) if row['alternative_questions'] else [],
            language=row['language'],
            category=row['category'],
            audio_path=row['audio_path'],
            audio_status=audio_status,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    # ========================================
    # Intent CRUD Operations
    # ========================================

    def create_intent(
        self,
        intent_name: str,
        description: str,
        trigger_phrases: List[str],
        action_type: str,
        action_config: Dict,
        language: str,
        category: str
    ) -> IntentEntry:
        """Create a new intent entry"""
        conn = self.get_connection()
        cursor = conn.cursor()

        intent_id = str(uuid.uuid4())
        created_at = datetime.now()
        updated_at = created_at

        cursor.execute('''
            INSERT INTO intent (
                intent_id, intent_name, description, trigger_phrases,
                action_type, action_config, language, category, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            intent_id,
            intent_name,
            description,
            json.dumps(trigger_phrases, ensure_ascii=False),
            action_type,
            json.dumps(action_config, ensure_ascii=False),
            language,
            category,
            created_at,
            updated_at
        ))

        conn.commit()
        conn.close()

        return IntentEntry(
            intent_id=intent_id,
            intent_name=intent_name,
            description=description,
            trigger_phrases=trigger_phrases,
            action_type=action_type,
            action_config=action_config,
            language=language,
            category=category,
            created_at=created_at,
            updated_at=updated_at
        )

    def get_intent_by_id(self, intent_id: str) -> Optional[IntentEntry]:
        """Get intent by intent_id"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM intent WHERE intent_id = ?', (intent_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_intent_entry(row)
        return None

    def get_intent_by_name(self, intent_name: str) -> Optional[IntentEntry]:
        """Get intent by intent_name"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM intent WHERE intent_name = ?', (intent_name,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_intent_entry(row)
        return None

    def get_all_intents(self) -> List[IntentEntry]:
        """Get all intent entries"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM intent ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_intent_entry(row) for row in rows]

    def update_intent(self, intent_id: str, updates: Dict) -> Optional[IntentEntry]:
        """Update intent entry"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        update_fields = []
        values = []

        if 'intent_name' in updates:
            update_fields.append('intent_name = ?')
            values.append(updates['intent_name'])

        if 'description' in updates:
            update_fields.append('description = ?')
            values.append(updates['description'])

        if 'trigger_phrases' in updates:
            update_fields.append('trigger_phrases = ?')
            values.append(json.dumps(updates['trigger_phrases'], ensure_ascii=False))

        if 'action_type' in updates:
            update_fields.append('action_type = ?')
            values.append(updates['action_type'])

        if 'action_config' in updates:
            update_fields.append('action_config = ?')
            values.append(json.dumps(updates['action_config'], ensure_ascii=False))

        if 'language' in updates:
            update_fields.append('language = ?')
            values.append(updates['language'])

        if 'category' in updates:
            update_fields.append('category = ?')
            values.append(updates['category'])

        update_fields.append('updated_at = ?')
        values.append(datetime.now())

        values.append(intent_id)

        query = f"UPDATE intent SET {', '.join(update_fields)} WHERE intent_id = ?"
        cursor.execute(query, values)

        conn.commit()
        conn.close()

        return self.get_intent_by_id(intent_id)

    def delete_intent(self, intent_id: str) -> bool:
        """Delete intent entry"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM intent WHERE intent_id = ?', (intent_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    def _row_to_intent_entry(self, row) -> IntentEntry:
        """Convert database row to IntentEntry object"""
        return IntentEntry(
            intent_id=row['intent_id'],
            intent_name=row['intent_name'],
            description=row['description'],
            trigger_phrases=json.loads(row['trigger_phrases']) if row['trigger_phrases'] else [],
            action_type=row['action_type'],
            action_config=json.loads(row['action_config']) if row['action_config'] else {},
            language=row['language'],
            category=row['category'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    # ========================================
    # Query Logs Operations
    # ========================================

    def create_query_log(
        self,
        query_text: str,
        matched_type: Optional[str] = None,
        matched_id: Optional[str] = None,
        matched_question: Optional[str] = None,
        confidence: Optional[float] = None,
        response_time: Optional[float] = None
    ) -> str:
        """Create a new query log entry"""
        from .models import QueryLog

        conn = self.get_connection()
        cursor = conn.cursor()

        log_id = str(uuid.uuid4())
        created_at = datetime.now()

        cursor.execute('''
            INSERT INTO query_logs (
                log_id, query_text, matched_type, matched_id,
                matched_question, confidence, response_time, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_id,
            query_text,
            matched_type,
            matched_id,
            matched_question,
            confidence,
            response_time,
            created_at
        ))

        conn.commit()
        conn.close()

        return log_id

    def get_query_logs(self, limit: int = 100, offset: int = 0, matched_type: Optional[str] = None) -> List[Dict]:
        """Get query logs with optional filtering"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM query_logs'
        params = []

        # Add filter if specified
        if matched_type and matched_type != 'all':
            query += ' WHERE matched_type = ?'
            params.append(matched_type)

        query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Convert rows to dictionaries
        logs = []
        for row in rows:
            logs.append({
                'log_id': row['log_id'],
                'query_text': row['query_text'],
                'matched_type': row['matched_type'],
                'matched_id': row['matched_id'],
                'matched_question': row['matched_question'],
                'confidence': row['confidence'],
                'response_time': row['response_time'],
                'created_at': row['created_at']
            })

        return logs

    def get_query_stats(self, days: int = 7) -> Dict:
        """Get query statistics for dashboard"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Today's queries count
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM query_logs
            WHERE DATE(created_at) = DATE('now')
        ''')
        today_queries = cursor.fetchone()['count']

        # Total queries count
        cursor.execute('SELECT COUNT(*) as count FROM query_logs')
        total_queries = cursor.fetchone()['count']

        # Average response time
        cursor.execute('SELECT AVG(response_time) as avg_time FROM query_logs WHERE response_time IS NOT NULL')
        avg_response_time = cursor.fetchone()['avg_time'] or 0.0

        # Top 5 FAQs
        cursor.execute('''
            SELECT matched_question, COUNT(*) as count
            FROM query_logs
            WHERE matched_type = 'faq' AND matched_question IS NOT NULL
            GROUP BY matched_question
            ORDER BY count DESC
            LIMIT 5
        ''')
        top_faqs = [{'question': row['matched_question'], 'count': row['count']} for row in cursor.fetchall()]

        # Intent distribution
        cursor.execute('''
            SELECT matched_question, COUNT(*) as count
            FROM query_logs
            WHERE matched_type = 'intent' AND matched_question IS NOT NULL
            GROUP BY matched_question
            ORDER BY count DESC
        ''')
        intent_distribution = [{'intent_name': row['matched_question'], 'count': row['count']} for row in cursor.fetchall()]

        # Daily trend (last N days)
        cursor.execute(f'''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM query_logs
            WHERE created_at >= DATE('now', '-{days} days')
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        ''')
        daily_trend = [{'date': row['date'], 'count': row['count']} for row in cursor.fetchall()]

        conn.close()

        return {
            'today_queries': today_queries,
            'total_queries': total_queries,
            'avg_response_time': round(avg_response_time, 2),
            'top_faqs': top_faqs,
            'intent_distribution': intent_distribution,
            'daily_trend': daily_trend
        }


# Global database instance
db = Database()
