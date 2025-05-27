#!/usr/bin/env python3
"""
Check all scores in the database and provide deletion options
"""

import sqlite3
from datetime import datetime

def check_all_scores():
    """Show all scores in the database"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Get all scores, most recent first
        c.execute("""
            SELECT id, date, player_name, course, nine, total
            FROM scores 
            ORDER BY id DESC
            LIMIT 50
        """)
        
        all_scores = c.fetchall()
        
        if not all_scores:
            print("✅ No scores found in the database")
            return []
        
        print(f"📋 Most recent scores (showing last 50):")
        print("-" * 80)
        print(f"{'ID':<5} {'Date':<12} {'Player':<15} {'Course':<20} {'Nine':<6} {'Total':<6}")
        print("-" * 80)
        
        for score_id, date, player, course, nine, total in all_scores:
            course_short = (course[:17] + "...") if course and len(course) > 20 else (course or "Unknown")
            player_short = (player[:12] + "...") if player and len(player) > 15 else (player or "Unknown")
            print(f"{score_id:<5} {date:<12} {player_short:<15} {course_short:<20} {nine:<6} {total:<6}")
        
        print(f"\n📊 Total scores shown: {len(all_scores)}")
        return all_scores
        
    except Exception as e:
        print(f"❌ Error checking scores: {e}")
        return []
    
    finally:
        conn.close()

def delete_score_by_id(score_id):
    """Delete a specific score by ID"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Show what we're about to delete
        c.execute("SELECT date, player_name, course, nine, total FROM scores WHERE id = ?", (score_id,))
        score_data = c.fetchone()
        
        if not score_data:
            print(f"❌ No score found with ID {score_id}")
            return False
        
        date, player, course, nine, total = score_data
        print(f"\n📋 Score to delete:")
        print(f"   ID {score_id}: {player} - {total} pts")
        print(f"   Course: {course}, Nine: {nine}, Date: {date}")
        
        confirm = input(f"\nAre you sure you want to delete this score? (yes/no): ")
        
        if confirm.lower() == 'yes':
            c.execute("DELETE FROM scores WHERE id = ?", (score_id,))
            conn.commit()
            print(f"✅ Successfully deleted score ID {score_id}")
            return True
        else:
            print("❌ Deletion cancelled")
            return False
        
    except Exception as e:
        print(f"❌ Error deleting score: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def delete_multiple_scores():
    """Delete multiple scores by ID"""
    
    print("\n🗑️ Multiple Score Deletion")
    print("Enter score IDs separated by commas (e.g., 123,124,125)")
    print("Or enter 'cancel' to abort")
    
    ids_input = input("Score IDs to delete: ").strip()
    
    if ids_input.lower() == 'cancel':
        print("❌ Deletion cancelled")
        return
    
    try:
        # Parse the IDs
        score_ids = [int(id_str.strip()) for id_str in ids_input.split(',')]
        
        print(f"\n📋 You want to delete {len(score_ids)} scores:")
        
        # Show what will be deleted
        conn = sqlite3.connect('golf_scores.db')
        c = conn.cursor()
        
        valid_ids = []
        for score_id in score_ids:
            c.execute("SELECT date, player_name, course, nine, total FROM scores WHERE id = ?", (score_id,))
            score_data = c.fetchone()
            
            if score_data:
                date, player, course, nine, total = score_data
                print(f"   ID {score_id}: {player} - {total} pts ({course}, {nine}) on {date}")
                valid_ids.append(score_id)
            else:
                print(f"   ID {score_id}: ❌ NOT FOUND")
        
        if not valid_ids:
            print("❌ No valid scores found to delete")
            conn.close()
            return
        
        confirm = input(f"\nDelete {len(valid_ids)} scores? (yes/no): ")
        
        if confirm.lower() == 'yes':
            for score_id in valid_ids:
                c.execute("DELETE FROM scores WHERE id = ?", (score_id,))
            
            conn.commit()
            print(f"✅ Successfully deleted {len(valid_ids)} scores")
        else:
            print("❌ Deletion cancelled")
        
        conn.close()
        
    except ValueError:
        print("❌ Invalid input. Please enter numbers separated by commas.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 PGG Tour Score Management")
    print("=" * 50)
    
    scores = check_all_scores()
    
    if not scores:
        print("No scores to delete.")
        exit()
    
    print("\n🗑️ Deletion Options:")
    print("1. Delete single score by ID")
    print("2. Delete multiple scores by ID")
    print("3. Exit without deleting")
    
    choice = input("\nChoose option (1-3): ")
    
    if choice == "1":
        try:
            score_id = int(input("Enter score ID to delete: "))
            delete_score_by_id(score_id)
        except ValueError:
            print("❌ Invalid ID")
    elif choice == "2":
        delete_multiple_scores()
    else:
        print("👋 Exiting without changes")
