#!/usr/bin/env python3
"""Check all data in the local SQLite database"""

import sqlite3

conn = sqlite3.connect('golf_scores.db')
c = conn.cursor()

# Get all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]

print("📊 Tables in local database:")
print("=" * 60)

for table in tables:
    if table == 'sqlite_sequence':
        continue
    
    try:
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        print(f"\n✅ {table}: {count} entries")
        
        if count > 0:
            # Get column names
            c.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in c.fetchall()]
            print(f"   Columns: {', '.join(columns)}")
            
            # Show first entry as sample
            c.execute(f"SELECT * FROM {table} LIMIT 1")
            row = c.fetchone()
            if row:
                print(f"   Sample: {dict(zip(columns, row))}")
    except Exception as e:
        print(f"\n⚠️ {table}: Error - {e}")

print("\n" + "=" * 60)
conn.close()

