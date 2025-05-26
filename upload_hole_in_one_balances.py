import sqlite3
from datetime import datetime

def upload_sample_balances():
    """Upload sample current balances for testing"""
    
    # Sample current balances (replace with your actual data)
    sample_balances = [
        ("Dan Plato", 25.00),
        ("Curtis Howell", 15.50),
        ("Andrew Salata", 50.00),  # At max
        ("Brett Vogelsberger", 8.00),
        ("Chris Lembach", 32.00),
        ("Dan Hanna", 12.50),
    ]
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    updated_count = 0
    
    try:
        for player_name, amount in sample_balances:
            # Cap at $50
            amount = min(amount, 50.0)
            
            # Update or insert player balance
            c.execute("""
                INSERT OR REPLACE INTO hole_in_one_pot 
                (player_name, amount_owed, total_contributed, last_updated)
                VALUES (?, ?, 0.0, ?)
            """, (player_name, amount, datetime.now().isoformat()))
            
            updated_count += 1
            print(f"✅ Updated {player_name}: ${amount:.2f}")
        
        conn.commit()
        print(f"\n✅ Updated {updated_count} player balances")
        
        # Show updated pot status
        show_updated_pot_status(c)
        
    except Exception as e:
        print(f"❌ Error uploading balances: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def show_updated_pot_status(cursor):
    """Display updated pot status"""
    
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
        
        print(f"\n💰 Updated Hole-in-One Pot Status:")
        print("=" * 50)
        print(f"🏆 Total Pot Amount: ${total_pot:.2f}")
        print(f"👥 Players Contributing: {len(balances)}")
        
        print(f"\n📊 Player Balances:")
        print("-" * 50)
        for player, owed, contributed in balances:
            status = " 🎯 MAX" if owed >= 50.0 else ""
            print(f"{player:<20} | Owes: ${owed:.2f}{status} | Paid: ${contributed:.2f}")
        
        # Count players at max
        max_players = sum(1 for _, owed, _ in balances if owed >= 50.0)
        if max_players > 0:
            print(f"\n🎯 Players at $50 cap: {max_players}")
        
    except Exception as e:
        print(f"❌ Error showing pot status: {e}")

def create_balance_template():
    """Create a template file for balance uploads"""
    
    template = """# Hole-in-One Balance Upload Template
# Format: Player Name,Amount Owed
# Lines starting with # are ignored
# Amounts will be automatically capped at $50.00
#
# Example entries:
Dan Plato,25.00
Curtis Howell,15.50
Andrew Salata,50.00
Brett Vogelsberger,8.00

# Add your current player balances below:
# Player Name,Amount

"""
    
    with open("hole_in_one_balances_template.txt", "w") as f:
        f.write(template)
    
    print("📝 Created 'hole_in_one_balances_template.txt'")
    print("   Edit this file with your current balances")
    print("   Then copy/paste the content into the Hole-in-One page upload section")

def test_50_dollar_cap():
    """Test the $50 cap functionality"""
    
    print("🧪 Testing $50 cap functionality...")
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Test player with amount over $50
        test_amount = 75.00
        capped_amount = min(test_amount, 50.0)
        
        c.execute("""
            INSERT OR REPLACE INTO hole_in_one_pot 
            (player_name, amount_owed, total_contributed, last_updated)
            VALUES (?, ?, 0.0, ?)
        """, ("Test Player", capped_amount, datetime.now().isoformat()))
        
        conn.commit()
        
        # Verify the cap worked
        c.execute("SELECT amount_owed FROM hole_in_one_pot WHERE player_name = 'Test Player'")
        result = c.fetchone()
        
        if result and result[0] == 50.0:
            print(f"✅ Cap test passed: ${test_amount:.2f} → ${result[0]:.2f}")
        else:
            print(f"❌ Cap test failed: Expected $50.00, got ${result[0]:.2f}")
        
        # Clean up test data
        c.execute("DELETE FROM hole_in_one_pot WHERE player_name = 'Test Player'")
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error testing cap: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("💰 Hole-in-One Balance Upload Utility")
    print("=" * 50)
    
    choice = input("\nChoose an option:\n1. Upload sample balances\n2. Create upload template\n3. Test $50 cap\n4. Show current status\n\nEnter choice (1-4): ")
    
    if choice == "1":
        print("\n📥 Uploading sample balances...")
        upload_sample_balances()
    elif choice == "2":
        create_balance_template()
    elif choice == "3":
        test_50_dollar_cap()
    elif choice == "4":
        conn = sqlite3.connect('golf_scores.db')
        c = conn.cursor()
        show_updated_pot_status(c)
        conn.close()
    else:
        print("❌ Invalid choice")
    
    print("\n✅ Done!")
