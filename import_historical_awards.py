import sqlite3

def import_sample_awards():
    """Import sample historical awards data"""
    
    # Sample historical awards data
    # Format: (season, category, player, description, date)
    sample_awards = [
        # 2023 Season
        ("2023 Season", "Season Champion", "Dan Plato", "Winner of the 2023 PGG Tour season", "2023-10-31"),
        ("2023 Season", "Most Improved Player", "Curtis Howell", "Showed remarkable improvement throughout the season", "2023-10-31"),
        ("2023 Season", "Best Average Score", "Andrew Salata", "Lowest average score for the season", "2023-10-31"),
        ("2023 Season", "Most Wins", "Chris Lembach", "Most individual round victories", "2023-10-31"),
        ("2023 Season", "Rookie of the Year", "Brett Vogelsberger", "Outstanding performance in first season", "2023-10-31"),
        
        # 2022 Season
        ("2022 Season", "Season Champion", "Andrew Salata", "2022 PGG Tour champion", "2022-10-31"),
        ("2022 Season", "Most Improved Player", "Dan Hanna", "Greatest improvement from previous season", "2022-10-31"),
        ("2022 Season", "Most Consistent", "Curtis Howell", "Most consistent scoring throughout season", "2022-10-31"),
        ("2022 Season", "Sportsmanship Award", "Chris Lembach", "Exemplary sportsmanship and team spirit", "2022-10-31"),
        
        # 2021 Season
        ("2021 Season", "Season Champion", "Curtis Howell", "2021 PGG Tour champion", "2021-10-31"),
        ("2021 Season", "Most Improved Player", "Dan Plato", "Significant improvement in play", "2021-10-31"),
        ("2021 Season", "Best Average Score", "Andrew Salata", "Lowest scoring average", "2021-10-31"),
        ("2021 Season", "Hole in One Club", "Brett Vogelsberger", "Achieved hole in one during season", "2021-08-15"),
    ]
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    imported_count = 0
    duplicate_count = 0
    
    try:
        for season, category, player, description, award_date in sample_awards:
            try:
                # Check if award already exists
                c.execute("""
                    SELECT COUNT(*) FROM awards 
                    WHERE season = ? AND award_category = ? AND player_name = ?
                """, (season, category, player))
                
                if c.fetchone()[0] == 0:
                    c.execute("""
                        INSERT INTO awards (season, award_category, player_name, description, award_date, created_by)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (season, category, player, description, award_date, "Historical Import"))
                    
                    imported_count += 1
                    print(f"✅ Added: {category} - {player} ({season})")
                else:
                    duplicate_count += 1
                    print(f"⚠️ Skipped duplicate: {category} - {player} ({season})")
                    
            except Exception as e:
                print(f"❌ Error importing {category} for {player}: {e}")
        
        conn.commit()
        
        print(f"\n📊 Import Summary:")
        print(f"✅ Successfully imported: {imported_count} awards")
        print(f"⚠️ Skipped duplicates: {duplicate_count} awards")
        
        # Show final count
        c.execute("SELECT COUNT(*) FROM awards")
        total_count = c.fetchone()[0]
        print(f"🏆 Total awards in database: {total_count}")
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def show_current_awards():
    """Display current awards in the database"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT season, award_category, player_name, description, award_date
        FROM awards
        ORDER BY season DESC, award_category, player_name
    """)
    
    awards = c.fetchall()
    
    if awards:
        print("\n🏆 Current Awards in Database:")
        print("=" * 80)
        
        current_season = None
        for season, category, player, description, award_date in awards:
            if season != current_season:
                print(f"\n📅 {season}")
                print("-" * 40)
                current_season = season
            
            print(f"🏆 {category:<20} | {player:<20} | {description[:30]}")
    else:
        print("\n❌ No awards found in database")
    
    conn.close()

def create_custom_import_template():
    """Create a template for custom historical data import"""
    
    template = """# PGG Tour Historical Awards Import Template
# Format: Season,Category,Player,Description,Date
# Lines starting with # are ignored
# 
# Example entries:
2023 Season,Season Champion,Your Player Name,Description of achievement,2023-10-31
2023 Season,Most Improved Player,Another Player,Showed great improvement,2023-10-31
2022 Season,Season Champion,Previous Champion,2022 season winner,2022-10-31

# Add your historical awards below:
# Season,Category,Player,Description,Date

"""
    
    with open("historical_awards_template.txt", "w") as f:
        f.write(template)
    
    print("📝 Created 'historical_awards_template.txt'")
    print("   Edit this file with your historical awards data")
    print("   Then copy/paste the content into the Awards page import section")

if __name__ == "__main__":
    print("🏆 PGG Tour Awards Import Utility")
    print("=" * 50)
    
    choice = input("\nChoose an option:\n1. Import sample awards\n2. Show current awards\n3. Create import template\n\nEnter choice (1-3): ")
    
    if choice == "1":
        print("\n📥 Importing sample historical awards...")
        import_sample_awards()
    elif choice == "2":
        show_current_awards()
    elif choice == "3":
        create_custom_import_template()
    else:
        print("❌ Invalid choice")
    
    print("\n✅ Done!")
