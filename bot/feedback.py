import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

DB_PATH = "feedback.db"


def init_db():
    """Initialize feedback database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            rating TEXT NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Feedback database initialized")


def save_feedback(
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    rating: str,
    comment: Optional[str] = None
):
    """Save user feedback to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO feedback (user_id, username, first_name, last_name, rating, comment)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, username, first_name, last_name, rating, comment))

    conn.commit()
    feedback_id = cursor.lastrowid
    conn.close()

    logger.info(f"Saved feedback #{feedback_id} from user {user_id}: {rating}")
    return feedback_id


def get_all_feedback() -> List[Dict]:
    """Get all feedback from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM feedback
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_feedback_stats() -> Dict:
    """Get feedback statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN rating = 'positive' THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN rating = 'negative' THEN 1 ELSE 0 END) as negative
        FROM feedback
    """)

    row = cursor.fetchone()
    conn.close()

    return {
        'total': row[0],
        'positive': row[1],
        'negative': row[2]
    }


def format_feedback_list(feedback_list: List[Dict]) -> str:
    """Format feedback list for display"""
    if not feedback_list:
        return "📭 Пока нет отзывов"

    stats = get_feedback_stats()

    lines = [
        "📊 Статистика отзывов:",
        f"Всего: {stats['total']}",
        f"👍 Положительных: {stats['positive']}",
        f"👎 Отрицательных: {stats['negative']}",
        "",
        "📝 Последние отзывы:",
        ""
    ]

    for fb in feedback_list[:20]:  # Показываем последние 20
        # Format user info
        user_display = fb['username'] or f"User {fb['user_id']}"
        if fb['first_name']:
            user_display = fb['first_name']
            if fb['last_name']:
                user_display += f" {fb['last_name']}"

        # Format rating
        rating_emoji = "👍" if fb['rating'] == 'positive' else "👎"

        # Format date
        date = fb['created_at'][:16]  # YYYY-MM-DD HH:MM

        lines.append(f"#{fb['id']} | {rating_emoji} | {user_display} | {date}")

        if fb['comment']:
            # Truncate long comments
            comment = fb['comment'][:100]
            if len(fb['comment']) > 100:
                comment += "..."
            lines.append(f"   💬 {comment}")

        lines.append("")

    return "\n".join(lines)
