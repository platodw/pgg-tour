from db_helper import get_db
import os

def setup_awards_table():
    """Create awards table for storing award winners"""
    
    conn = get_db()
    c = conn.cursor()
    
    # Check if we're using Postgres
    using_postgres = os.environ.get('DATABASE_URL') is not None
    
    try:
        # Create awards table (compatible with both SQLite and Postgres)
        if using_postgres:
            c.execute('''
            CREATE TABLE IF NOT EXISTS awards (
                id SERIAL PRIMARY KEY,
                season TEXT NOT NULL,
                award_category TEXT NOT NULL,
                player_name TEXT NOT NULL,
                description TEXT,
                award_date TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT DEFAULT 'Admin'
            )
            ''')
        else:
            c.execute('''
            CREATE TABLE IF NOT EXISTS awards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season TEXT NOT NULL,
                award_category TEXT NOT NULL,
                player_name TEXT NOT NULL,
                description TEXT,
                award_date TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT DEFAULT 'Admin'
            )
            ''')
        
        print("✅ Awards table created successfully")
        
        # Note: Sample awards removed - awards should be added manually through the web interface
        
        conn.commit()
        
        # Show current awards count
        c.execute("SELECT COUNT(*) FROM awards")
        count = c.fetchone()[0]
        print(f"📊 Total awards in database: {count}")
        
        # Show award categories
        c.execute("SELECT DISTINCT award_category FROM awards ORDER BY award_category")
        categories = [row[0] for row in c.fetchall()]
        print(f"🏆 Award categories: {', '.join(categories) if categories else 'None'}")
        
    except Exception as e:
        print(f"❌ Error creating awards table: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def show_awards_structure():
    """Display the awards table structure for reference"""
    
    print("\n📋 Awards Table Structure:")
    print("=" * 50)
    print("id              - Auto-incrementing primary key")
    print("season          - Golf season (e.g., '2024 Season')")
    print("award_category  - Type of award (e.g., 'Season Champion')")
    print("player_name     - Name of award winner")
    print("description     - Award description/details")
    print("award_date      - Date award was given")
    print("created_date    - When record was created")
    print("created_by      - Who created the record")
    print("\n🏆 Suggested Award Categories:")
    print("- Season Champion")
    print("- Most Improved Player")
    print("- Best Average Score")
    print("- Most Consistent")
    print("- Rookie of the Year")
    print("- Most Wins")
    print("- Hole in One Club")
    print("- Sportsmanship Award")

if __name__ == "__main__":
    print("🏆 Setting up awards table...")
    setup_awards_table()
    show_awards_structure()
