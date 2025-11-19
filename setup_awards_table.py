import sqlite3

def setup_awards_table():
    """Create awards table for storing award winners"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Create awards table
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
        
        # Add some sample award categories for reference
        sample_awards = [
            ("2024 Season", "Season Champion", "Sample Player", "Winner of the 2024 season", "2024-10-31"),
            ("2024 Season", "Most Improved", "Sample Player 2", "Showed the most improvement", "2024-10-31"),
            ("2023 Season", "Season Champion", "Sample Player 3", "Winner of the 2023 season", "2023-10-31"),
        ]
        
        # Insert sample data (will be ignored if already exists)
        for award in sample_awards:
            season, award_category, player_name, description, award_date = award
            # Check if this exact award already exists
            c.execute('''
                SELECT COUNT(*) FROM awards 
                WHERE season = ? AND award_category = ? AND player_name = ?
            ''', (season, award_category, player_name))
            
            exists = c.fetchone()[0] > 0
            
            if not exists:
                try:
                    c.execute('''
                        INSERT INTO awards (season, award_category, player_name, description, award_date)
                        VALUES (?, ?, ?, ?, ?)
                    ''', award)
                except Exception as e:
                    print(f"⚠️ Warning: Could not insert sample award {award}: {e}")
        
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
