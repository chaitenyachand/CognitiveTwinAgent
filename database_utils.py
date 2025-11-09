# database_utils.py
''' import mysql.connector
from mysql.connector import Error
import json
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_tables():
    """Creates all necessary tables if they don't exist."""
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    
    queries = [
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS topics (
            topic_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            topic_name VARCHAR(255) NOT NULL,
            source_type ENUM('text', 'pdf', 'predefined') NOT NULL,
            content_summary TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS mindmaps (
            mindmap_id INT AUTO_INCREMENT PRIMARY KEY,
            topic_id INT NOT NULL UNIQUE,
            mindmap_markdown TEXT, 
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS flashcards (
            flashcard_id INT AUTO_INCREMENT PRIMARY KEY,
            topic_id INT NOT NULL UNIQUE,
            flashcard_json JSON,
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS quiz_results (
            quiz_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            topic_id INT NOT NULL,
            score DECIMAL(5, 2) NOT NULL,
            total_questions INT NOT NULL,
            weak_areas JSON,
            date_taken TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS progress (
            progress_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL UNIQUE,
            total_topics INT DEFAULT 0,
            completed_topics INT DEFAULT 0,
            average_score DECIMAL(5, 2) DEFAULT 0.00,
            weak_topics_list JSON,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """
    ]
    
    try:
        for query in queries:
            cursor.execute(query)
        conn.commit()
    except Error as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()
        conn.close()

# --- User Functions ---

def create_user(username, email, password_hash):
    """Creates a new user and their initial progress record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Create user
        query = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, email, password_hash))
        user_id = cursor.lastrowid
        
        # Create initial progress record
        progress_query = "INSERT INTO progress (user_id) VALUES (%s)"
        cursor.execute(progress_query, (user_id,))
        
        conn.commit()
        return user_id
    except Error as e:
        print(f"Error creating user: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_by_username(username):
    """Fetches a user by their username."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# --- Topic & Content Functions ---

def create_topic(user_id, topic_name, source_type, content_summary):
    """Stores a new topic summary."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO topics (user_id, topic_name, source_type, content_summary) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, topic_name, source_type, content_summary))
        topic_id = cursor.lastrowid
        conn.commit()
        return topic_id
    except Error as e:
        print(f"Error creating topic: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def save_mindmap(topic_id, mindmap_markdown):
    """Saves or updates mindmap markdown string for a topic_id. (UPSERT)"""
    conn = get_db_connection()
    if conn is None: return
    
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO mindmaps (topic_id, mindmap_markdown) 
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE mindmap_markdown = %s
        """
        cursor.execute(query, (topic_id, mindmap_markdown, mindmap_markdown))
        conn.commit()
    except Error as e:
        print(f"Error saving/updating mindmap: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def save_flashcards(topic_id, flashcard_data):
    """Saves or updates flashcard JSON data for a topic_id. (UPSERT)"""
    conn = get_db_connection()
    if conn is None: return
    
    cursor = conn.cursor()
    try:
        flashcard_json = json.dumps(flashcard_data)
        query = """
        INSERT INTO flashcards (topic_id, flashcard_json)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE flashcard_json = %s
        """
        cursor.execute(query, (topic_id, flashcard_json, flashcard_json))
        conn.commit()
    except Error as e:
        print(f"Error saving/updating flashcards: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_topics_by_user(user_id):
    """Fetches all topics for a given user."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM topics WHERE user_id = %s ORDER BY date_created DESC"
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching topics: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_topic_content(topic_id):
    """Fetches summary, mindmap, and flashcards for a topic.
       This is now more robust and won't fail if one piece is missing.
    """
    conn = get_db_connection()
    if conn is None:
        print("Error: Could not connect to DB for get_topic_content")
        return None
        
    cursor = conn.cursor(dictionary=True)
    # Start with a default data structure
    data = {'summary': None, 'mindmap': None, 'flashcards': None}
    
    try:
        # Get Summary
        cursor.execute("SELECT content_summary FROM topics WHERE topic_id = %s", (topic_id,))
        summary_result = cursor.fetchone()
        if summary_result:
            data['summary'] = summary_result.get('content_summary')
        
        # Get Mindmap
        cursor.execute("SELECT mindmap_markdown FROM mindmaps WHERE topic_id = %s", (topic_id,))
        mindmap_result = cursor.fetchone()
        if mindmap_result:
            data['mindmap'] = mindmap_result['mindmap_markdown']
        
        # Get Flashcards
        cursor.execute("SELECT flashcard_json FROM flashcards WHERE topic_id = %s", (topic_id,))
        flashcard_result = cursor.fetchone()
        if flashcard_result and flashcard_result['flashcard_json']:
            # Check for empty json string 'null'
            if flashcard_result['flashcard_json'] != 'null':
                 data['flashcards'] = json.loads(flashcard_result['flashcard_json'])
            
        return data
        
    except Exception as e:
        print(f"Error fetching topic content: {e}")
        return None # Return None only if a DB error occurs
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def get_topic_by_name(user_id, topic_name):
    """Fetches a topic's ID and summary by its name."""
    conn = get_db_connection()
    if conn is None: return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT topic_id, content_summary FROM topics WHERE user_id = %s AND topic_name = %s"
        cursor.execute(query, (user_id, topic_name))
        return cursor.fetchone() # Returns {'topic_id': X, 'content_summary': '...'}
    except Error as e:
        print(f"Error fetching topic by name: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_topic_name_by_id(topic_id):
    """Fetches a topic's name by its ID."""
    conn = get_db_connection()
    if conn is None: return None
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT topic_name FROM topics WHERE topic_id = %s"
        cursor.execute(query, (topic_id,))
        result = cursor.fetchone()
        return result['topic_name'] if result else None
    except Error as e:
        print(f"Error fetching topic name by id: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# --- Quiz & Progress Functions ---

def save_quiz_result(user_id, topic_id, score, total_questions, weak_areas):
    """Saves the result of a quiz attempt."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO quiz_results (user_id, topic_id, score, total_questions, weak_areas) 
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, topic_id, score, total_questions, json.dumps(weak_areas)))
        conn.commit()
        
        # After saving, update the main progress table
        update_user_progress(user_id, topic_id, score, weak_areas)
        
    except Error as e:
        print(f"Error saving quiz result: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_quiz_results_by_user(user_id):
    """Fetches all quiz results for a user, joined with topic names."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        SELECT qr.*, t.topic_name 
        FROM quiz_results qr
        JOIN topics t ON qr.topic_id = t.topic_id
        WHERE qr.user_id = %s
        ORDER BY qr.date_taken ASC
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching quiz results: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_quiz_results_by_topic(user_id, topic_id):
    """Fetches all quiz results for a user for a specific topic."""
    conn = get_db_connection()
    if conn is None:
        return []
        
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        SELECT score, date_taken 
        FROM quiz_results
        WHERE user_id = %s AND topic_id = %s
        ORDER BY date_taken ASC
        """
        cursor.execute(query, (user_id, topic_id))
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching topic quiz results: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# --- CRITICALLY UPDATED FUNCTION ---
def update_user_progress(user_id, topic_id, latest_score, new_weak_areas):
    """Updates the user's main progress dashboard.
       Stores weak topics as a dictionary {main_topic: [sub_topic_1, ...]}
       and automatically cleans the list based on score.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get current progress
        cursor.execute("SELECT * FROM progress WHERE user_id = %s", (user_id,))
        progress = cursor.fetchone()
        
        # Get all topics
        cursor.execute("SELECT COUNT(DISTINCT topic_id) as total FROM topics WHERE user_id = %s", (user_id,))
        total_topics = cursor.fetchone()['total']
        
        # Get all scores
        cursor.execute("SELECT score FROM quiz_results WHERE user_id = %s", (user_id,))
        scores = [row['score'] for row in cursor.fetchall()]
        
        # Get completed topics (score >= 70)
        cursor.execute("""
            SELECT COUNT(DISTINCT topic_id) as completed
            FROM (
                SELECT topic_id, MAX(score) as max_score
                FROM quiz_results
                WHERE user_id = %s
                GROUP BY topic_id
            ) as max_scores
            WHERE max_score >= 70
        """, (user_id,))
        completed_topics = cursor.fetchone()['completed']

        # Calculate new average score
        new_avg_score = sum(scores) / len(scores) if scores else 0
        
        # --- NEW WEAK TOPIC LOGIC ---
        # Load the weak topics dictionary
        current_weak_dict = json.loads(progress['weak_topics_list']) if progress['weak_topics_list'] else {}
        topic_name = get_topic_name_by_id(topic_id)

        if not topic_name:
            print(f"Warning: Could not find topic name for topic_id {topic_id}. Skipping weak topic update.")
            raise Error("Topic name not found")

        if latest_score < 70:
            # Add or update the list of weak sub-topics for this main topic
            current_weak_dict[topic_name] = list(set(new_weak_areas)) # Use only the latest sub-topics
        else:
            # Score is good, remove the main topic (and all its sub-topics) from the dict
            if topic_name in current_weak_dict:
                del current_weak_dict[topic_name]
            
        updated_weak_list_json = json.dumps(current_weak_dict)
        # --- END NEW LOGIC ---
        
        # Update the progress table
        update_query = """
        UPDATE progress
        SET total_topics = %s, completed_topics = %s, average_score = %s, weak_topics_list = %s
        WHERE user_id = %s
        """
        cursor.execute(update_query, (
            total_topics,
            completed_topics,
            new_avg_score,
            updated_weak_list_json,
            user_id
        ))
        conn.commit()
        
    except Error as e:
        print(f"Error updating user progress: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_user_progress(user_id):
    """Fetches the main progress data for the dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM progress WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error fetching user progress: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
'''

# database_utils.py
import mysql.connector
from mysql.connector import Error
import json
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_tables():
    """Creates all necessary tables if they don't exist."""
    conn = get_db_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    
    queries = [
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS topics (
            topic_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            topic_name VARCHAR(255) NOT NULL,
            source_type ENUM('text', 'pdf', 'predefined', 'ocr') NOT NULL,
            content_summary TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS mindmaps (
            mindmap_id INT AUTO_INCREMENT PRIMARY KEY,
            topic_id INT NOT NULL UNIQUE,
            mindmap_markdown TEXT, 
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS flashcards (
            flashcard_id INT AUTO_INCREMENT PRIMARY KEY,
            topic_id INT NOT NULL UNIQUE,
            flashcard_json JSON,
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS formula_sheets (
            formula_sheet_id INT AUTO_INCREMENT PRIMARY KEY,
            topic_id INT NOT NULL UNIQUE,
            formula_sheet_markdown TEXT,
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS quiz_results (
            quiz_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            topic_id INT NOT NULL,
            score DECIMAL(5, 2) NOT NULL,
            total_questions INT NOT NULL,
            weak_areas JSON,
            date_taken TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS progress (
            progress_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL UNIQUE,
            total_topics INT DEFAULT 0,
            completed_topics INT DEFAULT 0,
            average_score DECIMAL(5, 2) DEFAULT 0.00,
            weak_topics_list JSON,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """
    ]
    
    try:
        for query in queries:
            cursor.execute(query)
        conn.commit()
    except Error as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()
        conn.close()

# --- User Functions (unchanged) ---
def create_user(username, email, password_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, email, password_hash))
        user_id = cursor.lastrowid
        progress_query = "INSERT INTO progress (user_id) VALUES (%s)"
        cursor.execute(progress_query, (user_id,))
        conn.commit()
        return user_id
    except Error as e:
        print(f"Error creating user: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# --- Topic & Content Functions ---
def create_topic(user_id, topic_name, source_type, content_summary):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO topics (user_id, topic_name, source_type, content_summary) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (user_id, topic_name, source_type, content_summary))
        topic_id = cursor.lastrowid
        conn.commit()
        return topic_id
    except Error as e:
        print(f"Error creating topic: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def save_mindmap(topic_id, mindmap_markdown):
    """Saves or updates mindmap markdown string for a topic_id. (UPSERT)"""
    conn = get_db_connection()
    if conn is None: return
    
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO mindmaps (topic_id, mindmap_markdown) 
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE mindmap_markdown = %s
        """
        cursor.execute(query, (topic_id, mindmap_markdown, mindmap_markdown))
        conn.commit()
    except Error as e:
        print(f"Error saving/updating mindmap: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def save_flashcards(topic_id, flashcard_data):
    """Saves or updates flashcard JSON data for a topic_id. (UPSERT)"""
    conn = get_db_connection()
    if conn is None: return
    
    cursor = conn.cursor()
    try:
        flashcard_json = json.dumps(flashcard_data)
        query = """
        INSERT INTO flashcards (topic_id, flashcard_json)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE flashcard_json = %s
        """
        cursor.execute(query, (topic_id, flashcard_json, flashcard_json))
        conn.commit()
    except Error as e:
        print(f"Error saving/updating flashcards: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# --- NEW FUNCTION ---
def save_formula_sheet(topic_id, markdown):
    """Saves or updates formula sheet markdown for a topic_id. (UPSERT)"""
    conn = get_db_connection()
    if conn is None: return
    
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO formula_sheets (topic_id, formula_sheet_markdown)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE formula_sheet_markdown = %s
        """
        cursor.execute(query, (topic_id, markdown, markdown))
        conn.commit()
    except Error as e:
        print(f"Error saving/updating formula sheet: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_topics_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM topics WHERE user_id = %s ORDER BY date_created DESC"
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching topics: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# --- MODIFIED FUNCTION ---
def get_topic_content(topic_id):
    """Fetches all materials for a topic."""
    conn = get_db_connection()
    if conn is None:
        print("Error: Could not connect to DB for get_topic_content")
        return None
        
    cursor = conn.cursor(dictionary=True)
    data = {'summary': None, 'mindmap': None, 'flashcards': None, 'formula_sheet': None}
    
    try:
        # Get Summary
        cursor.execute("SELECT content_summary FROM topics WHERE topic_id = %s", (topic_id,))
        summary_result = cursor.fetchone()
        if summary_result:
            data['summary'] = summary_result.get('content_summary')
        
        # Get Mindmap
        cursor.execute("SELECT mindmap_markdown FROM mindmaps WHERE topic_id = %s", (topic_id,))
        mindmap_result = cursor.fetchone()
        if mindmap_result:
            data['mindmap'] = mindmap_result['mindmap_markdown']
        
        # Get Flashcards
        cursor.execute("SELECT flashcard_json FROM flashcards WHERE topic_id = %s", (topic_id,))
        flashcard_result = cursor.fetchone()
        if flashcard_result and flashcard_result['flashcard_json']:
            if flashcard_result['flashcard_json'] != 'null':
                 data['flashcards'] = json.loads(flashcard_result['flashcard_json'])
        
        # Get Formula Sheet
        cursor.execute("SELECT formula_sheet_markdown FROM formula_sheets WHERE topic_id = %s", (topic_id,))
        formula_result = cursor.fetchone()
        if formula_result:
            data['formula_sheet'] = formula_result['formula_sheet_markdown']
            
        return data
        
    except Exception as e:
        print(f"Error fetching topic content: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# --- (Rest of functions are unchanged from previous step) ---
def get_topic_by_name(user_id, topic_name):
    conn = get_db_connection()
    if conn is None: return None
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT topic_id, content_summary FROM topics WHERE user_id = %s AND topic_name = %s"
        cursor.execute(query, (user_id, topic_name))
        return cursor.fetchone()
    except Error as e:
        print(f"Error fetching topic by name: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def get_topic_name_by_id(topic_id):
    conn = get_db_connection()
    if conn is None: return None
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT topic_name FROM topics WHERE topic_id = %s"
        cursor.execute(query, (topic_id,))
        result = cursor.fetchone()
        return result['topic_name'] if result else None
    except Error as e:
        print(f"Error fetching topic name by id: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def save_quiz_result(user_id, topic_id, score, total_questions, weak_areas):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO quiz_results (user_id, topic_id, score, total_questions, weak_areas) 
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, topic_id, score, total_questions, json.dumps(weak_areas)))
        conn.commit()
        update_user_progress(user_id, topic_id, score, weak_areas)
    except Error as e:
        print(f"Error saving quiz result: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_quiz_results_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
        SELECT qr.*, t.topic_name 
        FROM quiz_results qr
        JOIN topics t ON qr.topic_id = t.topic_id
        WHERE qr.user_id = %s
        ORDER BY qr.date_taken ASC
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching quiz results: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_quiz_results_by_topic(user_id, topic_id):
    conn = get_db_connection()
    if conn is None: return []
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT score, date_taken FROM quiz_results WHERE user_id = %s AND topic_id = %s ORDER BY date_taken ASC"
        cursor.execute(query, (user_id, topic_id))
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching topic quiz results: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def update_user_progress(user_id, topic_id, latest_score, new_weak_areas):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM progress WHERE user_id = %s", (user_id,))
        progress = cursor.fetchone()
        cursor.execute("SELECT COUNT(DISTINCT topic_id) as total FROM topics WHERE user_id = %s", (user_id,))
        total_topics = cursor.fetchone()['total']
        cursor.execute("SELECT score FROM quiz_results WHERE user_id = %s", (user_id,))
        scores = [row['score'] for row in cursor.fetchall()]
        cursor.execute("""
            SELECT COUNT(DISTINCT topic_id) as completed
            FROM (
                SELECT topic_id, MAX(score) as max_score
                FROM quiz_results
                WHERE user_id = %s
                GROUP BY topic_id
            ) as max_scores
            WHERE max_score >= 70
        """, (user_id,))
        completed_topics = cursor.fetchone()['completed']
        new_avg_score = sum(scores) / len(scores) if scores else 0
        
        # --- START OF THE FIX ---
        # 1. Load the data, defaulting to an empty dict if nothing is there
        loaded_data = json.loads(progress['weak_topics_list']) if progress and progress['weak_topics_list'] else {}

        # 2. CRITICAL FIX: Ensure the loaded data is a dictionary.
        # If it's a list (from old buggy data), reset it.
        if not isinstance(loaded_data, dict):
            print(f"Warning: Corrupted 'weak_topics_list' for user {user_id}. Resetting.")
            current_weak_dict = {}
        else:
            current_weak_dict = loaded_data
        # --- END OF THE FIX ---

        topic_name = get_topic_name_by_id(topic_id)
        if not topic_name:
            print(f"Warning: Could not find topic name for topic_id {topic_id}. Skipping weak topic update.")
            # Raising an Error here might be too aggressive, consider just returning
            raise ValueError(f"Topic name not found for topic_id {topic_id}")
            
        if latest_score < 70:
            current_weak_dict[topic_name] = list(set(new_weak_areas))
        else:
            if topic_name in current_weak_dict:
                del current_weak_dict[topic_name]
                
        updated_weak_list_json = json.dumps(current_weak_dict)
        update_query = """
        UPDATE progress
        SET total_topics = %s, completed_topics = %s, average_score = %s, weak_topics_list = %s
        WHERE user_id = %s
        """
        cursor.execute(update_query, (
            total_topics,
            completed_topics,
            new_avg_score,
            updated_weak_list_json,
            user_id
        ))
        conn.commit()
    except Error as e:
        print(f"Error updating user progress: {e}")
        conn.rollback()
    except Exception as ex: # Catch other errors like the ValueError
        print(f"An unexpected error occurred in update_user_progress: {ex}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close() # Make sure to close the connection too

def get_user_progress(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM progress WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        return cursor.fetchone()
    except Error as e:
        print(f"Error fetching user progress: {e}")
        return None
    finally:
        cursor.close()
        conn.close()