import sqlite3

def add_original_balance_column():
    """Add original_balance column to track what players originally owed for undo functionality"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Check if the column already exists
        c.execute("PRAGMA table_info(hole_in_one_pot)")
        columns = [column[1] for column in c.fetchall()]
        
        if 'original_balance' not in columns:
            # Add the original_balance column
            c.execute("ALTER TABLE hole_in_one_pot ADD COLUMN original_balance REAL DEFAULT 0.0")
            print("✅ Added 'original_balance' column to hole_in_one_pot table")
            
            # Set original_balance to current amount_owed for existing records
            c.execute("""
                UPDATE hole_in_one_pot 
                SET original_balance = CASE 
                    WHEN paid = 1 THEN total_contributed 
                    ELSE amount_owed 
                END
            """)
            print("✅ Set original_balance for existing records")
            
        else:
            print("ℹ️ 'original_balance' column already exists")
        
        conn.commit()
        
        # Show current status
        c.execute("""
            SELECT player_name, amount_owed, original_balance, paid 
            FROM hole_in_one_pot 
            ORDER BY original_balance DESC
        """)
        balances = c.fetchall()
        
        print(f"\n📊 Updated Player Status:")
        print("-" * 70)
        for player, owed, original, paid in balances:
            paid_status = "✅ PAID" if paid else "❌ UNPAID"
            print(f"{player:<20} | Current: ${owed:.2f} | Original: ${original:.2f} | {paid_status}")
        
    except Exception as e:
        print(f"❌ Error adding original_balance column: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("💾 Adding original balance tracking...")
    add_original_balance_column()
