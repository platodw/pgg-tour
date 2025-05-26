import sqlite3

conn = sqlite3.connect('golf_scores.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    course TEXT,
    nine TEXT,
    player_name TEXT,
    mulligan TEXT,
    hole_1 INTEGER,
    hole_2 INTEGER,
    hole_3 INTEGER,
    hole_4 INTEGER,
    hole_5 INTEGER,
    hole_6 INTEGER,
    hole_7 INTEGER,
    hole_8 INTEGER,
    hole_9 INTEGER,
    total INTEGER,
    winner TEXT
)
''')

conn.commit()
conn.close()

print("✅ Database and table created.")
