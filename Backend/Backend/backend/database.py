import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = "crowd_faqs.db"

def get_db_connection():
    """Returns a sqlite3 connection that yields rows as dictionaries."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Creates the SQLite database tables and seeds them with mock data if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Clusters Table (FAQ groups)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clusters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        representative_question_id INTEGER,
        answer_text TEXT,
        ai_draft_text TEXT,
        priority_score REAL DEFAULT 0.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Questions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL,
        category TEXT NOT NULL,
        cluster_id INTEGER,
        user_identifier TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cluster_id) REFERENCES clusters (id) ON DELETE SET NULL,
        FOREIGN KEY (user_identifier) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 4. Votes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cluster_id INTEGER NOT NULL,
        user_identifier TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cluster_id) REFERENCES clusters (id) ON DELETE CASCADE,
        FOREIGN KEY (user_identifier) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE (cluster_id, user_identifier)
    );
    """)

    conn.commit()

    # Check if database is empty to seed sample mock data
    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        seed_mock_data(conn)

    conn.close()

def seed_mock_data(conn):
    """Seeds the database with high-quality mock data for testing."""
    cursor = conn.cursor()
    
    # Insert mock users
    users = [
        ("user_1", "Ganeshprabu", "user"),
        ("user_2", "Ritzy", "user"),
        ("user_3", "Chaitanya", "user"),
        ("user_4", "Warish_Admin", "admin"),
        ("user_5", "Vineel_Dev", "user")
    ]
    cursor.executemany("INSERT INTO users (id, username, role) VALUES (?, ?, ?);", users)

    # Insert sample clusters
    clusters = [
        # Cluster 1: Password reset issue
        (1, "How can I reset my forgotten account password?", "To reset your password, click on the 'Forgot Password' link on the login page and follow the email instructions.", "AI Draft: You can reset password by email.", 25.0),
        # Cluster 2: Pricing question
        (2, "What are the subscription plans available?", None, "AI Draft: We offer standard and premium subscription plans starting from $9.99/mo.", 15.0),
        # Cluster 3: Bug report
        (3, "The dashboard page freezes when loading big data.", None, "AI Draft: We are working on optimizing the dashboard load times in the next patch.", 8.5)
    ]
    for cid, rep, ans, draft, score in clusters:
        cursor.execute("""
        INSERT INTO clusters (id, representative_question_id, answer_text, ai_draft_text, priority_score) 
        VALUES (?, NULL, ?, ?, ?);
        """, (cid, ans, draft, score))

    # Insert questions belonging to these clusters
    questions = [
        ("I forgot my password, how to reset it?", "Account", 1, "user_1", "approved"),
        ("How to change password?", "Account", 1, "user_2", "approved"),
        ("Password reset not working.", "Account", 1, "user_3", "approved"),
        
        ("Is there a free trial or paid tier?", "Pricing", 2, "user_1", "pending"),
        ("How much does this platform cost?", "Pricing", 2, "user_5", "pending"),
        
        ("Dashboard crashes on loading dataset", "Bug", 3, "user_3", "pending")
    ]
    for text, cat, cid, uid, status in questions:
        cursor.execute("""
        INSERT INTO questions (question_text, category, cluster_id, user_identifier, status) 
        VALUES (?, ?, ?, ?, ?);
        """, (text, cat, cid, uid, status))

    # Update representative question IDs for the clusters
    cursor.execute("UPDATE clusters SET representative_question_id = 1 WHERE id = 1;")
    cursor.execute("UPDATE clusters SET representative_question_id = 4 WHERE id = 2;")
    cursor.execute("UPDATE clusters SET representative_question_id = 6 WHERE id = 3;")

    # Seed some initial votes
    votes = [
        (1, "user_1"),
        (1, "user_2"),
        (1, "user_3"),
        (2, "user_1"),
        (2, "user_5"),
        (3, "user_3")
    ]
    cursor.executemany("INSERT INTO votes (cluster_id, user_identifier) VALUES (?, ?);", votes)

    conn.commit()

def calculate_priority_score(conn, cluster_id):
    """
    Calculates a dynamic priority score for a cluster based on:
    - Number of upvotes (weight = 10.0 per vote)
    - Category relevance weight (Bug = +5, Feature Request = +3, Account = +2, General = +0)
    - Recency factor (subtracts 0.5 per hour since creation to favor new hot topics)
    """
    cursor = conn.cursor()

    # Get total votes
    cursor.execute("SELECT COUNT(*) FROM votes WHERE cluster_id = ?;", (cluster_id,))
    vote_count = cursor.fetchone()[0]

    # Get cluster creation time and category of representative question
    cursor.execute("""
        SELECT c.created_at, q.category 
        FROM clusters c
        LEFT JOIN questions q ON q.id = c.representative_question_id
        WHERE c.id = ?;
    """, (cluster_id,))
    row = cursor.fetchone()
    
    if not row:
        return 0.0

    created_at_str = row['created_at']
    category = row['category'] or "General"

    # Compute category weight
    category_weights = {
        "Bug": 5.0,
        "Feature Request": 3.0,
        "Account": 2.0,
        "General": 0.0
    }
    cat_weight = category_weights.get(category, 0.0)

    # Compute recency penalty (hours elapsed)
    try:
        # Standardize timestamp parsing
        if " " in created_at_str:
            created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
        else:
            created_at = datetime.fromisoformat(created_at_str)
    except Exception:
        created_at = datetime.now()

    # Ensure localized/UTC awareness
    now = datetime.now()
    hours_elapsed = (now - created_at).total_seconds() / 3600.0
    recency_penalty = hours_elapsed * 0.1 # Subtract 0.1 score point per hour elapsed

    # Final score formula
    priority_score = (vote_count * 10.0) + cat_weight - recency_penalty
    return max(0.0, round(priority_score, 2))

def update_cluster_score(conn, cluster_id):
    """Recalculates and updates the priority score for a specific cluster in the database."""
    score = calculate_priority_score(conn, cluster_id)
    cursor = conn.cursor()
    cursor.execute("UPDATE clusters SET priority_score = ? WHERE id = ?;", (score, cluster_id))
    conn.commit()
    return score
