#!/usr/bin/env python3
"""
Delete all scores from today's date
"""

import sqlite3
from datetime import datetime

def delete_todays_scores():
    """Delete all scores from today's date"""
    
    # Get today's date
    today = datetime.today().strftime('%Y-%m-%d')
    print(f"🗑️ Deleting all scores from: {today}")
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # First, show what we're about to delete
        c.execute("SELECT player_name, course, nine, total FROM scores WHERE date = ?", (today,))
        scores_to_delete = c.fetchall()
        
        if not scores_to_delete:
            print(f"✅ No scores found for {today}")
            return
        
        print(f"📋 Found {len(scores_to_delete)} scores to delete:")
        for player, course, nine, total in scores_to_delete:
            print(f"   - {player}: {total} points ({course}, {nine})")
        
        # Delete the scores
        c.execute("DELETE FROM scores WHERE date = ?", (today,))
        deleted_count = c.rowcount
        
        conn.commit()
        print(f"✅ Successfully deleted {deleted_count} scores from {today}")
        
    except Exception as e:
        print(f"❌ Error deleting scores: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🗑️ PGG Tour Score Deletion Tool")
    print("=" * 40)
    
    # Confirm before deleting
    confirm = input("Are you sure you want to delete ALL scores from today? (yes/no): ")
    
    if confirm.lower() == 'yes':
        delete_todays_scores()
    else:
        print("❌ Deletion cancelled")
