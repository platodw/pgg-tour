#!/usr/bin/env python3
"""
Check recent scores in the database
"""

import sqlite3
from datetime import datetime, timedelta

def check_recent_scores():
    """Show recent scores from the last few days"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Get scores from the last 7 days
        week_ago = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        c.execute("""
            SELECT date, player_name, course, nine, total, id
            FROM scores 
            WHERE date >= ?
            ORDER BY date DESC, id DESC
        """, (week_ago,))
        
        recent_scores = c.fetchall()
        
        if not recent_scores:
            print("✅ No scores found in the last 7 days")
            return
        
        print(f"📋 Recent scores (last 7 days):")
        print("-" * 60)
        
        current_date = None
        for date, player, course, nine, total, score_id in recent_scores:
            if date != current_date:
                current_date = date
                print(f"\n📅 {date}:")
            
            print(f"   ID {score_id}: {player} - {total} pts ({course}, {nine})")
        
        print(f"\n📊 Total recent scores: {len(recent_scores)}")
        
    except Exception as e:
        print(f"❌ Error checking scores: {e}")
    
    finally:
        conn.close()

def delete_specific_scores():
    """Delete specific scores by ID or date"""
    
    print("\n🗑️ Delete Options:")
    print("1. Delete by specific date (YYYY-MM-DD)")
    print("2. Delete by score ID")
    print("3. Cancel")
    
    choice = input("\nChoose option (1-3): ")
    
    if choice == "1":
        date_to_delete = input("Enter date to delete (YYYY-MM-DD): ")
        delete_by_date(date_to_delete)
    elif choice == "2":
        try:
            score_id = int(input("Enter score ID to delete: "))
            delete_by_id(score_id)
        except ValueError:
            print("❌ Invalid ID")
    else:
        print("❌ Cancelled")

def delete_by_date(date_str):
    """Delete all scores from a specific date"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Show what we're about to delete
        c.execute("SELECT id, player_name, course, nine, total FROM scores WHERE date = ?", (date_str,))
        scores_to_delete = c.fetchall()
        
        if not scores_to_delete:
            print(f"✅ No scores found for {date_str}")
            return
        
        print(f"📋 Found {len(scores_to_delete)} scores to delete from {date_str}:")
        for score_id, player, course, nine, total in scores_to_delete:
            print(f"   ID {score_id}: {player} - {total} pts ({course}, {nine})")
        
        confirm = input(f"\nDelete ALL {len(scores_to_delete)} scores from {date_str}? (yes/no): ")
        
        if confirm.lower() == 'yes':
            c.execute("DELETE FROM scores WHERE date = ?", (date_str,))
            deleted_count = c.rowcount
            conn.commit()
            print(f"✅ Successfully deleted {deleted_count} scores from {date_str}")
        else:
            print("❌ Deletion cancelled")
        
    except Exception as e:
        print(f"❌ Error deleting scores: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def delete_by_id(score_id):
    """Delete a specific score by ID"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Show what we're about to delete
        c.execute("SELECT date, player_name, course, nine, total FROM scores WHERE id = ?", (score_id,))
        score_data = c.fetchone()
        
        if not score_data:
            print(f"❌ No score found with ID {score_id}")
            return
        
        date, player, course, nine, total = score_data
        print(f"📋 Score to delete:")
        print(f"   ID {score_id}: {player} - {total} pts ({course}, {nine}) on {date}")
        
        confirm = input(f"\nDelete this score? (yes/no): ")
        
        if confirm.lower() == 'yes':
            c.execute("DELETE FROM scores WHERE id = ?", (score_id,))
            conn.commit()
            print(f"✅ Successfully deleted score ID {score_id}")
        else:
            print("❌ Deletion cancelled")
        
    except Exception as e:
        print(f"❌ Error deleting score: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔍 PGG Tour Score Checker")
    print("=" * 40)
    
    check_recent_scores()
    
    # Ask if user wants to delete anything
    delete_choice = input("\nWould you like to delete any scores? (yes/no): ")
    if delete_choice.lower() == 'yes':
        delete_specific_scores()
