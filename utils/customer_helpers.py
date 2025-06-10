import sqlite3
from datetime import datetime



CUSTOMERS_DB = "customers.db"
RESERVED_SUBDOMAINS = {"www", "admin", "api", "app", "mail"}

def init_customers_db():
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            subdomain TEXT UNIQUE NOT NULL,
            app_name TEXT NOT NULL,
            plan TEXT NOT NULL,
            admin_password TEXT NOT NULL,
            port INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            deployed INTEGER DEFAULT 0
        )
        """)
        conn.commit()


def subdomain_taken(subdomain):
    if subdomain in RESERVED_SUBDOMAINS:
        return True
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM customers WHERE subdomain = ?", (subdomain,))
        return cur.fetchone() is not None


def get_next_available_port(base_port=9100):
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("SELECT MAX(port) FROM customers")
        row = cur.fetchone()
        return base_port if row[0] is None else row[0] + 1







def insert_customer(email, subdomain, app_name, plan, password, port):
    with sqlite3.connect(CUSTOMERS_DB) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            subdomain TEXT UNIQUE NOT NULL,
            app_name TEXT NOT NULL,
            plan TEXT NOT NULL,
            admin_password TEXT NOT NULL,
            port INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            deployed INTEGER DEFAULT 0
        )
        """)

        cur.execute("""
        INSERT INTO customers (email, subdomain, app_name, plan, admin_password, port, created_at, deployed)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            email,
            subdomain,
            app_name,
            plan,
            password,  # ✅ plain-text for debugging
            port,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
