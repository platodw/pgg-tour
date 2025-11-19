#!/usr/bin/env python3
"""
Export SQLite database to SQL INSERT statements that can be imported into Postgres
This doesn't need any Postgres drivers - just reads from SQLite and writes SQL
"""

import sqlite3
from datetime import datetime

def export_to_sql():
    """Export SQLite data to SQL file compatible with Postgres"""
    
    print("📤 Exporting SQLite data to SQL file...")
    print("=" * 60)
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    sql_statements = []
    sql_statements.append("-- PGG Tour Database Export")
    sql_statements.append(f"-- Generated: {datetime.now()}")
    sql_statements.append("-- Compatible with PostgreSQL")
    sql_statements.append("")
    
    # Get all tables (in order to respect foreign keys)
    tables_order = ['players', 'scores', 'awards', 'events', 'event_participants', 
                    'hole_in_one_pot', 'hole_in_one_history', 'pot_contributions']
    
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [t[0] for t in c.fetchall()]
    
    for table in tables_order:
        if table not in all_tables:
            continue
            
        print(f"📊 Exporting {table}...")
        
        try:
            # Get all data
            c.execute(f"SELECT * FROM {table}")
            rows = c.fetchall()
            
            if not rows:
                print(f"   ℹ️ No data in {table}")
                continue
            
            # Get column names
            c.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in c.fetchall()]
            
            # Skip 'id' column for auto-increment tables
            insert_columns = [col for col in columns if col != 'id']
            
            print(f"   Found {len(rows)} entries")
            
            sql_statements.append(f"-- Table: {table}")
            sql_statements.append(f"-- {len(rows)} rows")
            sql_statements.append("")
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Build values list, converting as needed
                values = []
                for col in insert_columns:
                    val = row_dict[col]
                    
                    if val is None:
                        values.append("NULL")
                    elif isinstance(val, bool):
                        values.append("TRUE" if val else "FALSE")
                    elif isinstance(val, int) and col in ['paid', 'active']:
                        # Convert 0/1 to boolean for Postgres
                        values.append("TRUE" if val else "FALSE")
                    elif isinstance(val, str):
                        # Escape single quotes
                        escaped = val.replace("'", "''")
                        values.append(f"'{escaped}'")
                    elif isinstance(val, (int, float)):
                        values.append(str(val))
                    else:
                        escaped = str(val).replace("'", "''")
                        values.append(f"'{escaped}'")
                
                col_names_str = ', '.join(insert_columns)
                values_str = ', '.join(values)
                
                sql_statements.append(f"INSERT INTO {table} ({col_names_str}) VALUES ({values_str});")
            
            sql_statements.append("")
            print(f"   ✅ Exported {len(rows)} entries")
            
        except Exception as e:
            print(f"   ⚠️ Error exporting {table}: {e}")
            sql_statements.append(f"-- ERROR exporting {table}: {e}")
            sql_statements.append("")
    
    conn.close()
    
    # Write to file
    filename = "golf_scores_export.sql"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))
    
    print(f"\n✅ Export complete!")
    print(f"📁 File saved as: {filename}")
    print(f"📊 Total statements: {len([s for s in sql_statements if s.startswith('INSERT')])}")
    
    return filename

if __name__ == "__main__":
    export_to_sql()

