#!/usr/bin/env python3
"""
Database migration script for PGG Tour
Exports SQLite data to SQL format for production database
"""

import sqlite3
import json
from datetime import datetime

def export_sqlite_to_sql():
    """Export SQLite database to SQL statements"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    sql_statements = []
    
    # Get all table names
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    
    print("📊 Exporting tables:")
    
    for table_name in tables:
        table = table_name[0]
        if table == 'sqlite_sequence':
            continue
            
        print(f"  - {table}")
        
        # Get table schema
        c.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
        create_statement = c.fetchone()[0]
        sql_statements.append(f"-- Table: {table}")
        sql_statements.append(create_statement + ";")
        sql_statements.append("")
        
        # Get all data
        c.execute(f"SELECT * FROM {table}")
        rows = c.fetchall()
        
        if rows:
            # Get column names
            c.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in c.fetchall()]
            
            sql_statements.append(f"-- Data for {table}")
            for row in rows:
                values = []
                for value in row:
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, str):
                        # Escape single quotes
                        escaped = value.replace("'", "''")
                        values.append(f"'{escaped}'")
                    else:
                        values.append(str(value))
                
                columns_str = ", ".join(columns)
                values_str = ", ".join(values)
                sql_statements.append(f"INSERT INTO {table} ({columns_str}) VALUES ({values_str});")
            
            sql_statements.append("")
    
    conn.close()
    
    # Write to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"pgg_tour_export_{timestamp}.sql"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("-- PGG Tour Database Export\n")
        f.write(f"-- Generated: {datetime.now()}\n")
        f.write("-- Use this file to import data into production database\n\n")
        f.write("\n".join(sql_statements))
    
    print(f"✅ Database exported to: {filename}")
    print(f"📁 File size: {len(sql_statements)} statements")
    
    return filename

def create_backup():
    """Create a backup of current database"""
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"golf_scores_backup_{timestamp}.db"
    shutil.copy2('golf_scores.db', backup_name)
    print(f"💾 Backup created: {backup_name}")
    return backup_name

if __name__ == "__main__":
    print("🚀 PGG Tour Database Migration Tool")
    print("=" * 50)
    
    # Create backup first
    backup_file = create_backup()
    
    # Export to SQL
    sql_file = export_sqlite_to_sql()
    
    print("\n📋 Next Steps:")
    print("1. Upload the SQL file to your production database")
    print("2. Update app.py to use production database connection")
    print("3. Test the deployment")
    print(f"\n📁 Files created:")
    print(f"  - Backup: {backup_file}")
    print(f"  - Export: {sql_file}")
