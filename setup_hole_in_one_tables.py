import sqlite3
from datetime import datetime

def setup_hole_in_one_tables():
    """Create tables for hole-in-one pot tracking and history"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Create hole_in_one_pot table to track player contributions
        c.execute('''
        CREATE TABLE IF NOT EXISTS hole_in_one_pot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            amount_owed REAL DEFAULT 0.0,
            total_contributed REAL DEFAULT 0.0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create hole_in_one_history table to track actual hole-in-ones
        c.execute('''
        CREATE TABLE IF NOT EXISTS hole_in_one_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            course TEXT NOT NULL,
            hole_number INTEGER NOT NULL,
            event_date TEXT NOT NULL,
            pot_amount REAL NOT NULL,
            description TEXT,
            recorded_date TEXT DEFAULT CURRENT_TIMESTAMP,
            recorded_by TEXT DEFAULT 'Admin'
        )
        ''')
        
        # Create pot_contributions table to track individual contributions
        c.execute('''
        CREATE TABLE IF NOT EXISTS pot_contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            contribution_amount REAL NOT NULL,
            contribution_date TEXT NOT NULL,
            score_id INTEGER,
            description TEXT,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (score_id) REFERENCES scores (id)
        )
        ''')
        
        print("✅ Hole-in-one tables created successfully")
        
        # Initialize pot balances for existing players
        initialize_player_pot_balances(c)
        
        # Calculate contributions for existing scores
        calculate_existing_contributions(c)
        
        conn.commit()
        
        # Show current pot status
        show_pot_status(c)
        
    except Exception as e:
        print(f"❌ Error creating hole-in-one tables: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def initialize_player_pot_balances(cursor):
    """Initialize pot balances for all existing players"""
    
    try:
        # Get all unique players from scores table
        cursor.execute("SELECT DISTINCT player_name FROM scores WHERE player_name IS NOT NULL")
        players = cursor.fetchall()
        
        initialized_count = 0
        for (player_name,) in players:
            # Check if player already exists in pot table
            cursor.execute("SELECT COUNT(*) FROM hole_in_one_pot WHERE player_name = ?", (player_name,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO hole_in_one_pot (player_name, amount_owed, total_contributed)
                    VALUES (?, 0.0, 0.0)
                """, (player_name,))
                initialized_count += 1
        
        print(f"✅ Initialized pot balances for {initialized_count} players")
        
    except Exception as e:
        print(f"❌ Error initializing pot balances: {e}")

def calculate_existing_contributions(cursor):
    """Calculate contributions for existing scores"""
    
    try:
        # Count rounds per player to calculate what they owe
        cursor.execute("""
            SELECT player_name, COUNT(*) as round_count
            FROM scores 
            WHERE player_name IS NOT NULL
            GROUP BY player_name
        """)
        
        player_rounds = cursor.fetchall()
        
        for player_name, round_count in player_rounds:
            amount_owed = round_count * 1.0  # $1 per round
            
            cursor.execute("""
                UPDATE hole_in_one_pot 
                SET amount_owed = ?, last_updated = ?
                WHERE player_name = ?
            """, (amount_owed, datetime.now().isoformat(), player_name))
        
        print(f"✅ Calculated contributions for {len(player_rounds)} players")
        
    except Exception as e:
        print(f"❌ Error calculating contributions: {e}")

def show_pot_status(cursor):
    """Display current pot status"""
    
    try:
        # Get total pot amount
        cursor.execute("SELECT SUM(amount_owed) FROM hole_in_one_pot")
        total_pot = cursor.fetchone()[0] or 0.0
        
        # Get player balances
        cursor.execute("""
            SELECT player_name, amount_owed, total_contributed 
            FROM hole_in_one_pot 
            ORDER BY amount_owed DESC
        """)
        balances = cursor.fetchall()
        
        print(f"\n💰 Current Hole-in-One Pot Status:")
        print("=" * 50)
        print(f"🏆 Total Pot Amount: ${total_pot:.2f}")
        print(f"👥 Players Contributing: {len(balances)}")
        
        print(f"\n📊 Player Balances:")
        print("-" * 40)
        for player, owed, contributed in balances:
            print(f"{player:<20} | Owes: ${owed:.2f} | Paid: ${contributed:.2f}")
        
        # Check for hole-in-one history
        cursor.execute("SELECT COUNT(*) FROM hole_in_one_history")
        hole_in_one_count = cursor.fetchone()[0]
        print(f"\n🕳️ Hole-in-Ones Recorded: {hole_in_one_count}")
        
    except Exception as e:
        print(f"❌ Error showing pot status: {e}")

if __name__ == "__main__":
    print("🕳️ Setting up Hole-in-One tracking system...")
    setup_hole_in_one_tables()
