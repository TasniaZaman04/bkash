import sqlite3

def setup_database():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            wallet_number TEXT,
            verification_number TEXT
        )
    ''')
    conn.commit()
    conn.close()

setup_database()
