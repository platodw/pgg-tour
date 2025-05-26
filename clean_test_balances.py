import sqlite3

def clean_test_balances():
    """Remove test $1.00 balances and keep only real uploaded balances"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Show current balances before cleanup
        print("🔍 Current balances before cleanup:")
        c.execute("""
            SELECT player_name, amount_owed, total_contributed 
            FROM hole_in_one_pot 
            ORDER BY amount_owed DESC
        """)
        balances = c.fetchall()
        
        for player, owed, contributed in balances:
            print(f"  {player:<20} | Owes: ${owed:.2f} | Paid: ${contributed:.2f}")
        
        # Remove players with exactly $1.00 balance (test data)
        c.execute("DELETE FROM hole_in_one_pot WHERE amount_owed = 1.0")
        deleted_count = c.rowcount
        
        conn.commit()
        
        print(f"\n✅ Removed {deleted_count} test records with $1.00 balances")
        
        # Show updated balances after cleanup
        print("\n💰 Updated balances after cleanup:")
        c.execute("""
            SELECT player_name, amount_owed, total_contributed 
            FROM hole_in_one_pot 
            ORDER BY amount_owed DESC
        """)
        updated_balances = c.fetchall()
        
        if updated_balances:
            total_pot = sum(owed for _, owed, _ in updated_balances)
            print(f"🏆 Total Pot: ${total_pot:.2f}")
            print("-" * 40)
            
            for player, owed, contributed in updated_balances:
                status = " 🎯 MAX" if owed >= 50.0 else ""
                print(f"  {player:<20} | Owes: ${owed:.2f}{status} | Paid: ${contributed:.2f}")
        else:
            print("  No balances remaining")
        
    except Exception as e:
        print(f"❌ Error cleaning balances: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def show_all_balances():
    """Show all current balances for review"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        c.execute("""
            SELECT player_name, amount_owed, total_contributed, last_updated
            FROM hole_in_one_pot 
            ORDER BY amount_owed DESC
        """)
        balances = c.fetchall()
        
        if balances:
            total_pot = sum(owed for _, owed, _, _ in balances)
            print(f"💰 Current Hole-in-One Pot Status:")
            print("=" * 60)
            print(f"🏆 Total Pot: ${total_pot:.2f}")
            print(f"👥 Players: {len(balances)}")
            print("-" * 60)
            
            for player, owed, contributed, updated in balances:
                status = " 🎯 MAX" if owed >= 50.0 else ""
                test_indicator = " [TEST]" if owed == 1.0 else ""
                print(f"{player:<20} | ${owed:.2f}{status}{test_indicator} | Paid: ${contributed:.2f}")
        else:
            print("No balances found")
        
    except Exception as e:
        print(f"❌ Error showing balances: {e}")
    
    finally:
        conn.close()

def remove_specific_players():
    """Remove specific players by name"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Show current players
        c.execute("SELECT player_name, amount_owed FROM hole_in_one_pot ORDER BY player_name")
        players = c.fetchall()
        
        print("Current players in hole-in-one pot:")
        for i, (name, amount) in enumerate(players, 1):
            test_indicator = " [TEST - $1.00]" if amount == 1.0 else ""
            print(f"{i:2d}. {name} - ${amount:.2f}{test_indicator}")
        
        print("\nEnter player numbers to remove (comma-separated), or 'all1' to remove all $1.00 balances:")
        choice = input("Choice: ").strip()
        
        if choice.lower() == 'all1':
            c.execute("DELETE FROM hole_in_one_pot WHERE amount_owed = 1.0")
            deleted_count = c.rowcount
            print(f"✅ Removed {deleted_count} players with $1.00 balances")
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                for idx in sorted(indices, reverse=True):
                    if 0 <= idx < len(players):
                        player_name = players[idx][0]
                        c.execute("DELETE FROM hole_in_one_pot WHERE player_name = ?", (player_name,))
                        print(f"✅ Removed {player_name}")
            except ValueError:
                print("❌ Invalid input")
                return
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error removing players: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧹 Hole-in-One Balance Cleanup Utility")
    print("=" * 50)
    
    choice = input("\nChoose an option:\n1. Remove all $1.00 test balances\n2. Show all current balances\n3. Remove specific players\n\nEnter choice (1-3): ")
    
    if choice == "1":
        print("\n🧹 Removing test $1.00 balances...")
        clean_test_balances()
    elif choice == "2":
        print("\n📊 Current balances:")
        show_all_balances()
    elif choice == "3":
        print("\n🎯 Remove specific players:")
        remove_specific_players()
    else:
        print("❌ Invalid choice")
    
    print("\n✅ Done!")
