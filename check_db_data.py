#!/usr/bin/env python3
"""Check what data exists in the local SQLite database"""

import sqlite3

conn = sqlite3.connect('golf_scores.db')
c = conn.cursor()

# Get all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print("📊 Tables found:", tables)
print()

# Check hole-in-one tables
for table in ['hole_in_one_pot', 'hole_in_one_history', 'pot_contributions']:
    if table in tables:
        try:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            count = c.fetchone()[0]
            print(f"✅ {table}: {count} entries")
            
            if count > 0:
                # Show sample data
                c.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = c.fetchall()
                print(f"   Sample data:")
                for row in rows:
                    print(f"   {row}")
        except Exception as e:
            print(f"⚠️ {table}: Error - {e}")
    else:
        print(f"ℹ️ {table}: Table not found")

conn.close()

