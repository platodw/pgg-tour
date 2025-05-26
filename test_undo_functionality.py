import sqlite3

def test_undo_functionality():
    """Test the undo functionality for Joe Gogala"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Check Joe Gogala's current status
        c.execute("SELECT player_name, amount_owed, original_balance, paid FROM hole_in_one_pot WHERE player_name = 'Joe Gogala'")
        result = c.fetchone()
        
        if result:
            player, owed, original, paid = result
            print(f"📊 Joe Gogala Status:")
            print(f"   Amount Owed: ${owed:.2f}")
            print(f"   Original Balance: ${original:.2f}")
            print(f"   Paid Status: {'✅ PAID' if paid else '❌ UNPAID'}")
            
            if paid and original > 0:
                print(f"\n🔄 Testing undo functionality...")
                # Simulate undo - restore original balance
                c.execute("""
                    UPDATE hole_in_one_pot 
                    SET paid = 0, 
                        amount_owed = original_balance
                    WHERE player_name = 'Joe Gogala'
                """)
                conn.commit()
                
                # Check result
                c.execute("SELECT amount_owed, paid FROM hole_in_one_pot WHERE player_name = 'Joe Gogala'")
                new_result = c.fetchone()
                if new_result:
                    new_owed, new_paid = new_result
                    print(f"✅ Undo successful!")
                    print(f"   New Amount Owed: ${new_owed:.2f}")
                    print(f"   New Paid Status: {'✅ PAID' if new_paid else '❌ UNPAID'}")
            else:
                print(f"\n⚠️ Joe Gogala is not in a paid state or has no original balance to restore")
        else:
            print("❌ Joe Gogala not found in database")
        
        # Show all current statuses
        print(f"\n📊 All Player Statuses:")
        print("-" * 70)
        c.execute("""
            SELECT player_name, amount_owed, original_balance, paid 
            FROM hole_in_one_pot 
            ORDER BY amount_owed DESC
        """)
        all_players = c.fetchall()
        
        for player, owed, original, paid in all_players:
            paid_status = "✅ PAID" if paid else "❌ UNPAID"
            print(f"{player:<20} | ${owed:.2f} | Orig: ${original:.2f} | {paid_status}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_undo_functionality()
