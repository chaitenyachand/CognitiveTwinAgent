# database_utils.py
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "cognitivetwin.db"

def get_db_connection():
    """Creates or connects to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like access
    return conn


def create_tables():
    """Creates all necessary tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    queries = [
        # ------------------ Core Cognitive Twin Tables ------------------
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS topics (
            topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic_name TEXT NOT NULL,
            source_type TEXT CHECK(source_type IN ('text','pdf','predefined','ocr')) NOT NULL,
            content_summary TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS mindmaps (
            mindmap_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL UNIQUE,
            mindmap_markdown TEXT,
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS flashcards (
            flashcard_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL UNIQUE,
            flashcard_json TEXT,
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS formula_sheets (
            formula_sheet_id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL UNIQUE,
            formula_sheet_markdown TEXT,
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS quiz_results (
            quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic_id INTEGER NOT NULL,
            score REAL NOT NULL,
            total_questions INTEGER NOT NULL,
            weak_areas TEXT,
            date_taken TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS progress (
            progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            total_topics INTEGER DEFAULT 0,
            completed_topics INTEGER DEFAULT 0,
            average_score REAL DEFAULT 0.0,
            weak_topics_list TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """,

        # ------------------ Agora Voice Tutor Tables ------------------
        """
        CREATE TABLE IF NOT EXISTS voice_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic_name TEXT NOT NULL,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            total_turns INTEGER DEFAULT 0,
            avg_confidence REAL DEFAULT 0.0,
            summary_json TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS voice_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            topic_name TEXT,
            user_text TEXT,
            ai_text TEXT,
            metadata JSON,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES voice_sessions(session_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """
    ]

    for query in queries:
        cursor.execute(query)
    conn.commit()
    conn.close()

# ---------------------- User Functions ---------------------- #

def create_user(username, email, password_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO progress (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return user_id
    except sqlite3.Error as e:
        print(f"Error creating user: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        conn.close()


# ---------------------- Topic Functions ---------------------- #

def create_topic(user_id, topic_name, source_type, content_summary):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO topics (user_id, topic_name, source_type, content_summary) VALUES (?, ?, ?, ?)",
            (user_id, topic_name, source_type, content_summary)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error creating topic: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def save_mindmap(topic_id, mindmap_markdown):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO mindmaps (topic_id, mindmap_markdown)
            VALUES (?, ?)
            ON CONFLICT(topic_id) DO UPDATE SET mindmap_markdown = excluded.mindmap_markdown
        """, (topic_id, mindmap_markdown))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving mindmap: {e}")
        conn.rollback()
    finally:
        conn.close()


def save_flashcards(topic_id, flashcard_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        flashcard_json = json.dumps(flashcard_data)
        cursor.execute("""
            INSERT INTO flashcards (topic_id, flashcard_json)
            VALUES (?, ?)
            ON CONFLICT(topic_id) DO UPDATE SET flashcard_json = excluded.flashcard_json
        """, (topic_id, flashcard_json))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving flashcards: {e}")
        conn.rollback()
    finally:
        conn.close()


def save_formula_sheet(topic_id, markdown):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO formula_sheets (topic_id, formula_sheet_markdown)
            VALUES (?, ?)
            ON CONFLICT(topic_id) DO UPDATE SET formula_sheet_markdown = excluded.formula_sheet_markdown
        """, (topic_id, markdown))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error saving formula sheet: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_topics_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM topics WHERE user_id = ? ORDER BY date_created DESC", (user_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error fetching topics: {e}")
        return []
    finally:
        conn.close()


def get_topic_content(topic_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    data = {'summary': None, 'mindmap': None, 'flashcards': None, 'formula_sheet': None}
    try:
        cursor.execute("SELECT content_summary FROM topics WHERE topic_id = ?", (topic_id,))
        row = cursor.fetchone()
        if row:
            data['summary'] = row['content_summary']

        cursor.execute("SELECT mindmap_markdown FROM mindmaps WHERE topic_id = ?", (topic_id,))
        row = cursor.fetchone()
        if row:
            data['mindmap'] = row['mindmap_markdown']

        cursor.execute("SELECT flashcard_json FROM flashcards WHERE topic_id = ?", (topic_id,))
        row = cursor.fetchone()
        if row and row['flashcard_json']:
            data['flashcards'] = json.loads(row['flashcard_json'])

        cursor.execute("SELECT formula_sheet_markdown FROM formula_sheets WHERE topic_id = ?", (topic_id,))
        row = cursor.fetchone()
        if row:
            data['formula_sheet'] = row['formula_sheet_markdown']

        return data
    except sqlite3.Error as e:
        print(f"Error fetching topic content: {e}")
        return None
    finally:
        conn.close()


def get_topic_by_name(user_id, topic_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT topic_id, content_summary FROM topics WHERE user_id = ? AND topic_name = ?", (user_id, topic_name))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_topic_name_by_id(topic_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT topic_name FROM topics WHERE topic_id = ?", (topic_id,))
        row = cursor.fetchone()
        return row['topic_name'] if row else None
    finally:
        conn.close()


# ---------------------- Quiz & Progress ---------------------- #

def save_quiz_result(user_id, topic_id, score, total_questions, weak_areas):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO quiz_results (user_id, topic_id, score, total_questions, weak_areas)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, topic_id, score, total_questions, json.dumps(weak_areas)))
        conn.commit()
        update_user_progress(user_id, topic_id, score, weak_areas)
    except sqlite3.Error as e:
        print(f"Error saving quiz result: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_quiz_results_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT qr.*, t.topic_name
            FROM quiz_results qr
            JOIN topics t ON qr.topic_id = t.topic_id
            WHERE qr.user_id = ?
            ORDER BY qr.date_taken ASC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_quiz_results_by_topic(user_id, topic_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT score, date_taken
            FROM quiz_results
            WHERE user_id = ? AND topic_id = ?
            ORDER BY date_taken ASC
        """, (user_id, topic_id))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def update_user_progress(user_id, topic_id, latest_score, new_weak_areas):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM progress WHERE user_id = ?", (user_id,))
        progress = cursor.fetchone()

        cursor.execute("SELECT COUNT(DISTINCT topic_id) AS total FROM topics WHERE user_id = ?", (user_id,))
        total_topics = cursor.fetchone()['total']

        cursor.execute("SELECT score FROM quiz_results WHERE user_id = ?", (user_id,))
        scores = [row['score'] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT COUNT(DISTINCT topic_id) AS completed
            FROM (
                SELECT topic_id, MAX(score) AS max_score
                FROM quiz_results
                WHERE user_id = ?
                GROUP BY topic_id
            )
            WHERE max_score >= 70
        """, (user_id,))
        completed_topics = cursor.fetchone()['completed']

        new_avg_score = sum(scores) / len(scores) if scores else 0
        weak_list = json.loads(progress['weak_topics_list']) if progress and progress['weak_topics_list'] else {}
        if not isinstance(weak_list, dict):
            weak_list = {}

        topic_name = get_topic_name_by_id(topic_id)
        if latest_score < 70:
            weak_list[topic_name] = list(set(new_weak_areas))
        else:
            weak_list.pop(topic_name, None)

        cursor.execute("""
            UPDATE progress
            SET total_topics = ?, completed_topics = ?, average_score = ?, weak_topics_list = ?
            WHERE user_id = ?
        """, (total_topics, completed_topics, new_avg_score, json.dumps(weak_list), user_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating progress: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_user_progress(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM progress WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------- Agora Voice Functions ---------------------- #

def create_voice_session(user_id, topic_name):
    """Start a new voice session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO voice_sessions (user_id, topic_name) VALUES (?, ?)",
            (user_id, topic_name)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error creating voice session: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def log_conversation(user_id, session_id, topic_name, user_text, ai_text, metadata):
    """Logs one voice exchange (turn)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO voice_conversations (session_id, user_id, topic_name, user_text, ai_text, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, user_id, topic_name, user_text, ai_text, json.dumps(metadata)))
        conn.commit()
        cursor.execute("UPDATE voice_sessions SET total_turns = total_turns + 1 WHERE session_id = ?", (session_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error logging conversation: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_conversation_history(session_id):
    """Retrieve all user-AI exchanges for a session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT user_text, ai_text, metadata, timestamp
            FROM voice_conversations
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """, (session_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def end_voice_session(session_id, summary_data):
    """Mark session end and update summary."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE voice_sessions
            SET end_time = CURRENT_TIMESTAMP, summary_json = ?
            WHERE session_id = ?
        """, (json.dumps(summary_data), session_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error ending voice session: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_voice_sessions_by_user(user_id):
    """List all past voice tutoring sessions for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT session_id, topic_name, start_time, end_time, total_turns, avg_confidence
            FROM voice_sessions
            WHERE user_id = ?
            ORDER BY start_time DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


# Auto-create tables on first run
if not os.path.exists(DB_PATH):
    print("Creating new SQLite database and tables...")
create_tables()
