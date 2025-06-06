import sqlite3
import bcrypt

def insert_admin_user(db_path, email, password):
    print(f"🔐 Inserting admin: {email} into {db_path}")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Ensure Admin table exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)

    # Insert or update password if email already exists
    cur.execute("""
    INSERT INTO Admin (email, password_hash)
    VALUES (?, ?)
    ON CONFLICT(email) DO UPDATE SET password_hash = excluded.password_hash
    """, (email, hashed))

    conn.commit()
    conn.close()
