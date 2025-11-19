#!/usr/bin/env python3
"""
Import SQL file into Postgres on Heroku
Run this on Heroku using: heroku run python import_sql_to_postgres.py
"""

import os
import re
from db_helper import get_db

def import_sql_file(filename='golf_scores_export.sql'):
    """Import SQL file into Postgres"""
    
    print("📥 Importing SQL file into Postgres...")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        print("   Make sure the SQL export file is in the current directory")
        return False
    
    # Connect to Postgres
    try:
        conn = get_db()
        c = conn.cursor()
        print("✅ Connected to Postgres")
    except Exception as e:
        print(f"❌ Error connecting to Postgres: {e}")
        return False
    
    imported_count = 0
    error_count = 0
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by semicolon, but keep track of strings
        statements = []
        current = ""
        in_string = False
        escape_next = False
        
        for char in content:
            if escape_next:
                current += char
                escape_next = False
                continue
                
            if char == '\\' and in_string:
                escape_next = True
                current += char
                continue
                
            if char == "'" and not escape_next:
                in_string = not in_string
                current += char
                continue
                
            if char == ';' and not in_string:
                stmt = current.strip()
                if stmt and not stmt.startswith('--'):
                    statements.append(stmt)
                current = ""
            else:
                current += char
        
        # Add last statement if exists
        if current.strip() and not current.strip().startswith('--'):
            statements.append(current.strip())
        
        print(f"\n📊 Found {len(statements)} SQL statements")
        print("🔄 Importing...")
        
        for i, statement in enumerate(statements, 1):
            if not statement.strip() or statement.strip().startswith('--'):
                continue
                
            try:
                # Convert SQLite-style syntax to Postgres if needed
                # Replace ? with %s for prepared statements (but we're using direct execution)
                statement = statement.replace('?', '%s')
                
                # Execute statement
                c.execute(statement)
                imported_count += 1
                
                if i % 50 == 0:
                    print(f"   Progress: {i}/{len(statements)} statements...")
                    
            except Exception as e:
                error_count += 1
                print(f"   ⚠️ Error on statement {i}: {str(e)[:100]}")
                # Don't stop on errors - continue importing
        
        # Commit all changes
        conn.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ Import complete!")
        print(f"   Imported: {imported_count} statements")
        if error_count > 0:
            print(f"   Errors: {error_count} statements")
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 PGG Tour - SQL Import Tool")
    print("   Importing golf_scores_export.sql into Postgres")
    print("=" * 60)
    
    # Check if running on Heroku
    if os.environ.get('DATABASE_URL'):
        print("✅ DATABASE_URL is set (running on Heroku)")
    else:
        print("⚠️ DATABASE_URL not set - make sure you're running on Heroku")
    
    import_sql_file()

