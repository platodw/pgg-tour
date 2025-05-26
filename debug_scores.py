import sqlite3
from datetime import datetime

def get_season_label(date_obj):
    """
    Calculate season based on November 1 - October 31 year.
    Examples:
    - Nov 1, 2024 - Oct 31, 2025 = "2025 Season"
    - Nov 1, 2023 - Oct 31, 2024 = "2024 Season"
    """
    if date_obj.month >= 11:  # November or December
        return f"{date_obj.year + 1} Season"
    else:  # January through October
        return f"{date_obj.year} Season"

def debug_scores():
    """Debug the scores in the database to check season calculation"""

    conn = sqlite3.connect("golf_scores.db")
    c = conn.cursor()

    # Get all records with more details
    c.execute("""
        SELECT id, date, player_name, season, total
        FROM scores
        ORDER BY id DESC
    """)

    rows = c.fetchall()

    print("🔍 Database Records Analysis:")
    print("=" * 60)

    if not rows:
        print("❌ No records found in database")
        conn.close()
        return

    for row in rows:
        record_id, date_str, player_name, season, total = row

        print(f"Record ID: {record_id}")
        print(f"  Player: {player_name}")
        print(f"  Date: '{date_str}' (type: {type(date_str)})")
        print(f"  Season: {season}")
        print(f"  Total: {total}")

        # Try to parse the date and calculate what season should be
        if date_str and date_str.strip():
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                expected_season = get_season_label(date_obj)
                print(f"  Expected Season: {expected_season}")

                if season != expected_season:
                    print(f"  ⚠️  MISMATCH! Database has '{season}' but should be '{expected_season}'")
                else:
                    print(f"  ✅ Season calculation is correct")

            except ValueError as e:
                print(f"  ❌ Error parsing date: {e}")
        else:
            print(f"  ❌ Date is empty or None")

        print("-" * 40)

    conn.close()

if __name__ == "__main__":
    debug_scores()
