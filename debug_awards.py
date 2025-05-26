import sqlite3

def debug_awards():
    """Debug awards display issues"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    # Check all awards in database
    c.execute("SELECT * FROM awards ORDER BY season DESC, award_category")
    all_awards = c.fetchall()
    
    print("🔍 All Awards in Database:")
    print("=" * 80)
    
    if all_awards:
        for award in all_awards:
            print(f"ID: {award[0]}")
            print(f"Season: '{award[1]}'")
            print(f"Category: '{award[2]}'")
            print(f"Player: '{award[3]}'")
            print(f"Description: '{award[4]}'")
            print(f"Award Date: '{award[5]}'")
            print(f"Created: {award[6]}")
            print("-" * 40)
    else:
        print("❌ No awards found in database")
    
    # Check the grouping logic
    print("\n🔍 Testing Grouping Logic:")
    print("=" * 50)
    
    c.execute("""
        SELECT season, award_category, player_name, description, award_date
        FROM awards
        ORDER BY season DESC, award_category, player_name
    """)
    
    query_results = c.fetchall()
    
    # Group awards by season (same logic as Flask app)
    awards_by_season = {}
    for season, category, player, description, award_date in query_results:
        if season not in awards_by_season:
            awards_by_season[season] = []
        awards_by_season[season].append({
            'category': category,
            'player': player,
            'description': description,
            'award_date': award_date
        })
    
    print(f"Seasons found: {list(awards_by_season.keys())}")
    
    for season, awards in awards_by_season.items():
        print(f"\n📅 {season}: {len(awards)} awards")
        for award in awards:
            print(f"  🏆 {award['category']} - {award['player']}")
    
    conn.close()

if __name__ == "__main__":
    debug_awards()
