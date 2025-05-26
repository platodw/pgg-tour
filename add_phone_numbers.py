#!/usr/bin/env python3
"""
Add phone number field to players table for SMS notifications
"""

import sqlite3

def add_phone_field():
    """Add phone number field to existing players table"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Check if phone column already exists
        c.execute("PRAGMA table_info(players)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'phone' not in columns:
            # Add phone number column
            c.execute('ALTER TABLE players ADD COLUMN phone TEXT')
            print("✅ Added phone number field to players table")
        else:
            print("✅ Phone number field already exists")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error adding phone field: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("📱 Adding phone number support to PGG Tour...")
    add_phone_field()
    print("🎉 Database updated for SMS notifications!")
