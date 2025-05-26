import sqlite3

conn = sqlite3.connect("golf_scores.db")
c = conn.cursor()

c.execute("SELECT date, player_name, season FROM scores ORDER BY date DESC LIMIT 10")
rows = c.fetchall()

for row in rows:
    print(row)

conn.close()
