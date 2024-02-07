import sqlite3

def initialize_db():
    conn = sqlite3.connect('data/database.db')
    c = conn.cursor()
    # Create table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS counter
                 (name TEXT PRIMARY KEY, value INTEGER)''')
    # Initialize counter if it doesn't exist
    c.execute('''INSERT OR IGNORE INTO counter VALUES ('upload', 0)''')
    conn.commit()
    conn.close()

def increment_counter(counter_name):
    conn = sqlite3.connect('data/database.db')
    c = conn.cursor()
    # Increment counter
    c.execute('''UPDATE counter SET value = value + 1 WHERE name = ?''', (counter_name,))
    conn.commit()
    conn.close()

def get_counter(counter_name):
    conn = sqlite3.connect('data/database.db')
    c = conn.cursor()
    # Get current counter value
    c.execute('''SELECT value FROM counter WHERE name = ?''', (counter_name,))
    counter = c.fetchone()[0]
    conn.close()
    return counter