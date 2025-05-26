import sqlite3

def add_paid_status_column():
    """Add a 'paid' status column to the hole_in_one_pot table"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Check if the column already exists
        c.execute("PRAGMA table_info(hole_in_one_pot)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'paid' not in columns:
            # Add the paid column (0 = not paid, 1 = paid)
            c.execute("ALTER TABLE hole_in_one_pot ADD COLUMN paid INTEGER DEFAULT 0")
            print("✅ Added 'paid' status column to hole_in_one_pot table")
        else:
            print("ℹ️ 'paid' column already exists")
        
        conn.commit()
        
        # Show current status
        c.execute("""
            SELECT player_name, amount_owed, total_contributed, paid 
            FROM hole_in_one_pot 
            ORDER BY amount_owed DESC
        """)
        balances = c.fetchall()
        
        print(f"\n📊 Current Player Status:")
        print("-" * 60)
        for player, owed, contributed, paid in balances:
            paid_status = "✅ PAID" if paid else "❌ UNPAID"
            print(f"{player:<20} | ${owed:.2f} | {paid_status}")
        
    except Exception as e:
        print(f"❌ Error adding paid status column: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("💳 Adding paid status tracking...")
    add_paid_status_column()
