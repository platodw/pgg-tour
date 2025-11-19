#!/usr/bin/env python3
"""
Comprehensive migration script to transfer ALL data from local SQLite to Heroku Postgres
Reads from local golf_scores.db and writes to Postgres on Heroku
"""

import sqlite3
import os

# Try different Postgres drivers directly (avoid db_helper which needs psycopg2)
# Try psycopg2 first
try:
    import psycopg2
    def get_db():
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            return psycopg2.connect(database_url)
        raise Exception("DATABASE_URL not set")
    print("✅ Using psycopg2")
except ImportError:
    # Try pg8000 (pure Python)
    try:
        import pg8000.dbapi
        def get_db():
            import urllib.parse
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise Exception("DATABASE_URL not set")
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            url = urllib.parse.urlparse(database_url)
            return pg8000.dbapi.connect(
                host=url.hostname,
                port=url.port or 5432,
                user=url.username,
                password=url.password,
                database=url.path[1:]
            )
        print("✅ Using pg8000 (pure Python driver)")
    except ImportError:
        print("❌ Need either psycopg2-binary or pg8000 installed")
        print("   Try: pip install pg8000")
        raise

def migrate_table(sqlite_c, pg_c, table_name, skip_columns=None, check_duplicate=None, convert_bool=None):
    """
    Generic function to migrate a table from SQLite to Postgres
    
    Args:
        sqlite_c: SQLite cursor
        pg_c: Postgres cursor
        table_name: Name of the table to migrate
        skip_columns: List of column names to skip (e.g., ['id'] for auto-increment)
        check_duplicate: Function to check if row already exists, returns (check_query, check_params)
        convert_bool: List of column names that need boolean conversion
    """
    
    skip_columns = skip_columns or []
    convert_bool = convert_bool or []
    
    try:
        # Get all data from SQLite
        sqlite_c.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_c.fetchall()
        
        if not rows:
            print(f"   ℹ️ No {table_name} entries found")
            return 0
        
        # Get column names
        sqlite_c.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in sqlite_c.fetchall()]
        
        # Columns to insert (skip auto-increment columns)
        insert_columns = [col for col in columns if col not in skip_columns]
        
        print(f"   Found {len(rows)} entries")
        migrated_count = 0
        
        for row in rows:
            row_dict = dict(zip(columns, row))
            
            # Check for duplicates if function provided
            skip_row = False
            if check_duplicate:
                check_query, check_params = check_duplicate(row_dict)
                if check_query:
                    pg_c.execute(check_query, check_params)
                    exists = pg_c.fetchone()[0] > 0
                    if exists:
                        skip_row = True
            
            if skip_row:
                continue
            
            # Convert booleans if needed
            for col in convert_bool:
                if col in row_dict:
                    row_dict[col] = bool(row_dict[col]) if row_dict[col] is not None else False
            
            # Build INSERT statement
            col_names = ', '.join(insert_columns)
            placeholders = ', '.join(['%s'] * len(insert_columns))
            values = [row_dict[col] for col in insert_columns]
            
            pg_c.execute(f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})", values)
            migrated_count += 1
        
        print(f"   ✅ Migrated {migrated_count} entries")
        return migrated_count
        
    except Exception as e:
        print(f"   ⚠️ Error migrating {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def migrate_all_data():
    """Migrate all data from SQLite to Postgres"""
    
    print("🔄 Migrating ALL data from SQLite to Postgres...")
    print("=" * 60)
    
    # Connect to local SQLite database
    sqlite_conn = sqlite3.connect('golf_scores.db')
    sqlite_c = sqlite_conn.cursor()
    
    # Connect to Postgres (will use Heroku DATABASE_URL if set)
    try:
        pg_conn = get_db()
        pg_c = pg_conn.cursor()
        print("✅ Connected to Postgres")
        
        # Test the connection
        pg_c.execute("SELECT 1")
        pg_c.fetchone()
        print("✅ Connection test successful")
    except Exception as e:
        print(f"❌ Error connecting to Postgres: {e}")
        print("   Make sure DATABASE_URL environment variable is set for Heroku")
        import traceback
        traceback.print_exc()
        sqlite_conn.close()
        return False
    
    total_migrated = 0
    
    try:
        # Migrate in order to respect foreign keys
        
        # 1. Players (no dependencies)
        print("\n📊 Step 1: Migrating players...")
        count = migrate_table(
            sqlite_c, pg_c, 'players',
            skip_columns=['id'],
            check_duplicate=lambda d: (
                "SELECT COUNT(*) FROM players WHERE name = %s",
                (d['name'],)
            ),
            convert_bool=['active']
        )
        total_migrated += count
        
        # 2. Scores (depends on players by name, but names should match)
        print("\n📊 Step 2: Migrating scores (this may take a moment)...")
        count = migrate_table(
            sqlite_c, pg_c, 'scores',
            skip_columns=['id']
            # Don't check duplicates - allow all scores to migrate
        )
        total_migrated += count
        
        # 3. Awards (depends on players by name)
        print("\n📊 Step 3: Migrating awards...")
        count = migrate_table(
            sqlite_c, pg_c, 'awards',
            skip_columns=['id'],
            check_duplicate=lambda d: (
                """SELECT COUNT(*) FROM awards 
                   WHERE season = %s AND award_category = %s AND player_name = %s""",
                (d['season'], d['award_category'], d['player_name'])
            )
        )
        total_migrated += count
        
        # 4. Events (no dependencies)
        print("\n📊 Step 4: Migrating events...")
        count = migrate_table(
            sqlite_c, pg_c, 'events',
            skip_columns=['id']
        )
        total_migrated += count
        
        # 5. Event participants (depends on events and players)
        print("\n📊 Step 5: Migrating event_participants...")
        count = migrate_table(
            sqlite_c, pg_c, 'event_participants',
            skip_columns=['id']
        )
        total_migrated += count
        
        # 6. Hole-in-one pot (depends on players by name)
        print("\n📊 Step 6: Migrating hole_in_one_pot...")
        count = migrate_table(
            sqlite_c, pg_c, 'hole_in_one_pot',
            skip_columns=['id'],
            check_duplicate=lambda d: (
                "SELECT COUNT(*) FROM hole_in_one_pot WHERE player_name = %s",
                (d['player_name'],)
            ),
            convert_bool=['paid']
        )
        total_migrated += count
        
        # 7. Hole-in-one history (no dependencies)
        print("\n📊 Step 7: Migrating hole_in_one_history...")
        count = migrate_table(
            sqlite_c, pg_c, 'hole_in_one_history',
            skip_columns=['id'],
            check_duplicate=lambda d: (
                """SELECT COUNT(*) FROM hole_in_one_history 
                   WHERE player_name = %s AND course = %s AND hole_number = %s AND event_date = %s""",
                (d['player_name'], d['course'], d['hole_number'], d['event_date'])
            )
        )
        total_migrated += count
        
        # 8. Pot contributions (may depend on scores)
        print("\n📊 Step 8: Migrating pot_contributions...")
        # Handle score_id - if NULL, skip that column
        try:
            sqlite_c.execute("SELECT * FROM pot_contributions")
            contrib_rows = sqlite_c.fetchall()
            
            if contrib_rows:
                sqlite_c.execute("PRAGMA table_info(pot_contributions)")
                columns = [col[1] for col in sqlite_c.fetchall()]
                
                print(f"   Found {len(contrib_rows)} entries")
                contrib_count = 0
                
                for row in contrib_rows:
                    row_dict = dict(zip(columns, row))
                    
                    # Check if exists
                    pg_c.execute("""
                        SELECT COUNT(*) FROM pot_contributions 
                        WHERE player_name = %s AND contribution_amount = %s AND contribution_date = %s
                    """, (row_dict['player_name'], row_dict['contribution_amount'], row_dict['contribution_date']))
                    if pg_c.fetchone()[0] > 0:
                        continue
                    
                    # Remove score_id if NULL
                    insert_dict = {k: v for k, v in row_dict.items() if k != 'id'}
                    if 'score_id' in insert_dict and insert_dict['score_id'] is None:
                        insert_dict.pop('score_id')
                    
                    col_names = ', '.join(insert_dict.keys())
                    placeholders = ', '.join(['%s'] * len(insert_dict))
                    values = list(insert_dict.values())
                    
                    pg_c.execute(f"INSERT INTO pot_contributions ({col_names}) VALUES ({placeholders})", values)
                    contrib_count += 1
                
                print(f"   ✅ Migrated {contrib_count} entries")
                total_migrated += contrib_count
            else:
                print("   ℹ️ No pot_contributions entries found")
        except Exception as e:
            print(f"   ⚠️ Error migrating pot_contributions: {e}")
        
        # Commit all changes
        pg_conn.commit()
        print(f"\n{'='*60}")
        print(f"✅ Migration complete! Migrated {total_migrated} total entries")
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        pg_conn.rollback()
        return False
        
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    print("🚀 PGG Tour - Complete Database Migration Tool")
    print("   Migrating ALL data from local SQLite to Heroku Postgres")
    print("=" * 60)
    
    # Check if DATABASE_URL is set
    if not os.environ.get('DATABASE_URL'):
        print("\n⚠️ WARNING: DATABASE_URL not set!")
        print("   You need to set DATABASE_URL to migrate to Heroku Postgres")
        print("\n   To get your DATABASE_URL:")
        print("   1. Go to Heroku Dashboard → Your App → Settings")
        print("   2. Click 'Reveal Config Vars'")
        print("   3. Copy the DATABASE_URL value")
        print("\n   Then set it:")
        print("   Windows PowerShell: $env:DATABASE_URL = 'postgres://...'")
        print("   Windows CMD: set DATABASE_URL=postgres://...")
        print("   Mac/Linux: export DATABASE_URL='postgres://...'")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            exit(1)
    else:
        print(f"✅ DATABASE_URL is set")
    
    print("\n📋 This will migrate:")
    print("   - Players (20 entries)")
    print("   - Scores (312 entries)")
    print("   - Awards (17 entries)")
    print("   - Events")
    print("   - Event Participants")
    print("   - Hole-in-One Pot (20 entries)")
    print("   - Hole-in-One History")
    print("   - Pot Contributions")
    print("\n🚀 Starting migration in 2 seconds...")
    import time
    time.sleep(2)
    
    success = migrate_all_data()
    
    if success:
        print("\n🎉 Migration successful!")
        print("   All your data should now be in Postgres on Heroku")
        print("   Check your website to verify the data is there")
    else:
        print("\n⚠️ Migration had errors - check output above")
        print("   You may need to fix issues and run again")

