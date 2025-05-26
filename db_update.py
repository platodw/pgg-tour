import sqlite3

conn = sqlite3.connect("golf_scores.db")  # ✅ use the correct file name
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE scores ADD COLUMN season TEXT;")
    print("✅ 'season' column added successfully.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ️ 'season' column already exists.")
    elif "no such table" in str(e):
        print("❌ Table 'scores' not found. Double-check the table name.")
    else:
        print("❌ Error:", e)

conn.commit()
conn.close()