import sqlite3

def add_test_2025_award():
    """Add a test award for 2025 Season to verify display"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Add a test 2025 award
        c.execute("""
            INSERT INTO awards (season, award_category, player_name, description, award_date, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("2025 Season", "Test Award", "Dan Plato", "Test award for 2025 season display", "2025-05-25", "Test"))
        
        conn.commit()
        print("✅ Added test 2025 Season award")
        
        # Show all awards to verify
        c.execute("SELECT season, award_category, player_name FROM awards ORDER BY season DESC")
        awards = c.fetchall()
        
        print("\n📊 All Awards by Season:")
        current_season = None
        for season, category, player in awards:
            if season != current_season:
                print(f"\n{season}:")
                current_season = season
            print(f"  - {category}: {player}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    add_test_2025_award()
