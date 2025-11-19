#!/usr/bin/env python3
"""
Migration script to transfer data from local SQLite to Heroku Postgres
Reads from local golf_scores.db and writes to Postgres on Heroku
"""

import sqlite3
import os
from db_helper import get_db

def migrate_hole_in_one_data():
    """Migrate hole-in-one data from SQLite to Postgres"""
    
    print("🔄 Migrating hole-in-one data from SQLite to Postgres...")
    print("=" * 60)
    
    # Connect to local SQLite database
    sqlite_conn = sqlite3.connect('golf_scores.db')
    sqlite_c = sqlite_conn.cursor()
    
    # Connect to Postgres (will use Heroku DATABASE_URL if set)
    try:
        pg_conn = get_db()
        pg_c = pg_conn.cursor()
    except Exception as e:
        print(f"❌ Error connecting to Postgres: {e}")
        print("   Make sure DATABASE_URL environment variable is set for Heroku")
        sqlite_conn.close()
        return False
    
    migrated_count = 0
    
    try:
        # 1. Migrate hole_in_one_pot table
        print("\n📊 Migrating hole_in_one_pot...")
        try:
            sqlite_c.execute("SELECT * FROM hole_in_one_pot")
            pot_rows = sqlite_c.fetchall()
            
            if pot_rows:
                # Get column names
                sqlite_c.execute("PRAGMA table_info(hole_in_one_pot)")
                columns = [col[1] for col in sqlite_c.fetchall()]
                
                print(f"   Found {len(pot_rows)} entries")
                
                for row in pot_rows:
                    # Convert row to dict for easier handling
                    row_dict = dict(zip(columns, row))
                    player_name = row_dict['player_name']
                    
                    # Check if entry already exists
                    pg_c.execute("SELECT COUNT(*) FROM hole_in_one_pot WHERE player_name = %s", (player_name,))
                    exists = pg_c.fetchone()[0] > 0
                    
                    if not exists:
                        # Handle boolean conversion for Postgres
                        # SQLite stores booleans as 0/1, Postgres needs True/False
                        if 'paid' in row_dict:
                            row_dict['paid'] = bool(row_dict['paid']) if row_dict['paid'] is not None else False
                        
                        # Build INSERT statement, skip 'id' column (auto-increment)
                        insert_columns = [col for col in columns if col != 'id']
                        col_names = ', '.join(insert_columns)
                        placeholders = ', '.join(['%s'] * len(insert_columns))
                        values = [row_dict[col] for col in insert_columns]
                        
                        pg_c.execute(f"INSERT INTO hole_in_one_pot ({col_names}) VALUES ({placeholders})", values)
                        migrated_count += 1
                        print(f"   ✅ Migrated {player_name}: owes ${row_dict.get('amount_owed', 0):.2f}, contributed ${row_dict.get('total_contributed', 0):.2f}")
                    else:
                        print(f"   ⚠️ Skipping {player_name} - already exists")
                
                print(f"   ✅ Migrated {migrated_count} hole_in_one_pot entries")
            else:
                print("   ℹ️ No hole_in_one_pot entries found")
        except Exception as e:
            print(f"   ⚠️ Error migrating hole_in_one_pot: {e}")
        
        # 2. Migrate hole_in_one_history table
        print("\n📊 Migrating hole_in_one_history...")
        try:
            sqlite_c.execute("SELECT * FROM hole_in_one_history")
            history_rows = sqlite_c.fetchall()
            
            if history_rows:
                # Get column names
                sqlite_c.execute("PRAGMA table_info(hole_in_one_history)")
                columns = [col[1] for col in sqlite_c.fetchall()]
                
                print(f"   Found {len(history_rows)} entries")
                history_count = 0
                
                for row in history_rows:
                    # Check if entry already exists (by unique combination)
                    player_name = row[columns.index('player_name')]
                    course = row[columns.index('course')]
                    hole_number = row[columns.index('hole_number')]
                    event_date = row[columns.index('event_date')]
                    
                    pg_c.execute("""
                        SELECT COUNT(*) FROM hole_in_one_history 
                        WHERE player_name = %s AND course = %s AND hole_number = %s AND event_date = %s
                    """, (player_name, course, hole_number, event_date))
                    exists = pg_c.fetchone()[0] > 0
                    
                    if not exists:
                        # Build INSERT statement
                        placeholders = ', '.join(['%s'] * len(row))
                        col_names = ', '.join(columns)
                        
                        pg_c.execute(f"INSERT INTO hole_in_one_history ({col_names}) VALUES ({placeholders})", row)
                        history_count += 1
                
                print(f"   ✅ Migrated {history_count} hole_in_one_history entries")
                migrated_count += history_count
            else:
                print("   ℹ️ No hole_in_one_history entries found")
        except Exception as e:
            print(f"   ⚠️ Error migrating hole_in_one_history: {e}")
        
        # 3. Migrate pot_contributions table
        print("\n📊 Migrating pot_contributions...")
        try:
            sqlite_c.execute("SELECT * FROM pot_contributions")
            contrib_rows = sqlite_c.fetchall()
            
            if contrib_rows:
                # Get column names
                sqlite_c.execute("PRAGMA table_info(pot_contributions)")
                columns = [col[1] for col in sqlite_c.fetchall()]
                
                print(f"   Found {len(contrib_rows)} entries")
                contrib_count = 0
                
                for row in contrib_rows:
                    # Check if entry already exists (basic check by player_name, amount, date)
                    player_name = row[columns.index('player_name')]
                    amount = row[columns.index('contribution_amount')]
                    date = row[columns.index('contribution_date')]
                    
                    pg_c.execute("""
                        SELECT COUNT(*) FROM pot_contributions 
                        WHERE player_name = %s AND contribution_amount = %s AND contribution_date = %s
                    """, (player_name, amount, date))
                    exists = pg_c.fetchone()[0] > 0
                    
                    if not exists:
                        # Build INSERT statement (skip score_id if it doesn't exist or is NULL)
                        row_dict = dict(zip(columns, row))
                        
                        # Remove score_id if NULL (foreign key might not exist)
                        if 'score_id' in row_dict and row_dict['score_id'] is None:
                            row_dict.pop('score_id')
                        
                        col_names = ', '.join(row_dict.keys())
                        placeholders = ', '.join(['%s'] * len(row_dict))
                        values = list(row_dict.values())
                        
                        pg_c.execute(f"INSERT INTO pot_contributions ({col_names}) VALUES ({placeholders})", values)
                        contrib_count += 1
                
                print(f"   ✅ Migrated {contrib_count} pot_contributions entries")
                migrated_count += contrib_count
            else:
                print("   ℹ️ No pot_contributions entries found")
        except Exception as e:
            print(f"   ⚠️ Error migrating pot_contributions: {e}")
        
        # Commit all changes
        pg_conn.commit()
        print(f"\n✅ Migration complete! Migrated {migrated_count} total entries")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        pg_conn.rollback()
        return False
        
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    print("🚀 PGG Tour Database Migration Tool")
    print("   Migrating from local SQLite to Heroku Postgres")
    print("=" * 60)
    
    # Check if DATABASE_URL is set
    if not os.environ.get('DATABASE_URL'):
        print("\n⚠️ WARNING: DATABASE_URL not set!")
        print("   For local testing, this will try to connect to local database")
        print("   For Heroku migration, set DATABASE_URL first:")
        print("   export DATABASE_URL='postgres://...'  # (get from Heroku config)")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            exit(1)
    
    success = migrate_hole_in_one_data()
    
    if success:
        print("\n🎉 Migration successful!")
        print("   Your hole-in-one data should now be in Postgres")
    else:
        print("\n⚠️ Migration had errors - check output above")

