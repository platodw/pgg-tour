import sqlite3
import os

def clear_database():
    """Clear all records from the golf_scores database"""
    
    # Check if database exists
    if not os.path.exists('golf_scores.db'):
        print("❌ Database file 'golf_scores.db' not found.")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect('golf_scores.db')
        c = conn.cursor()
        
        # Check how many records exist before deletion
        c.execute("SELECT COUNT(*) FROM scores")
        record_count = c.fetchone()[0]
        
        if record_count == 0:
            print("ℹ️ Database is already empty - no records to delete.")
        else:
            # Delete all records from the scores table
            c.execute("DELETE FROM scores")
            
            # Commit the changes
            conn.commit()
            
            print(f"✅ Successfully deleted {record_count} records from the database.")
            print("🧹 Database is now clean and ready for testing!")
        
        # Close the connection
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🗑️ Clearing all records from golf_scores database...")
    clear_database()
