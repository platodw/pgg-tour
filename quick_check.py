#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('golf_scores.db')
c = conn.cursor()

# Check if scores table exists and get recent scores
try:
    c.execute("SELECT COUNT(*) FROM scores")
    total_count = c.fetchone()[0]
    print(f"Total scores in database: {total_count}")
    
    if total_count > 0:
        c.execute("SELECT id, date, player_name, total FROM scores ORDER BY id DESC LIMIT 10")
        recent = c.fetchall()
        print("\nMost recent scores:")
        for score_id, date, player, total in recent:
            print(f"ID {score_id}: {player} - {total} pts on {date}")
    
except Exception as e:
    print(f"Error: {e}")

conn.close()
