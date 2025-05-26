import sqlite3
import os

def setup_schedule_tables():
    """Create tables for players and scheduled events"""
    
    conn = sqlite3.connect('golf_scores.db')
    c = conn.cursor()
    
    try:
        # Create players table
        c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            email TEXT,
            phone TEXT,
            active BOOLEAN DEFAULT 1,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create events table
        c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            event_time TEXT,
            course TEXT,
            description TEXT,
            max_players INTEGER DEFAULT 4,
            created_by TEXT,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'scheduled'
        )
        ''')
        
        # Create event_participants table (many-to-many relationship)
        c.execute('''
        CREATE TABLE IF NOT EXISTS event_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            player_id INTEGER,
            status TEXT DEFAULT 'invited',
            invited_date TEXT DEFAULT CURRENT_TIMESTAMP,
            response_date TEXT,
            FOREIGN KEY (event_id) REFERENCES events (id),
            FOREIGN KEY (player_id) REFERENCES players (id),
            UNIQUE(event_id, player_id)
        )
        ''')
        
        print("✅ Schedule tables created successfully")
        
        # Migrate existing players from players.txt
        migrate_players_from_txt(c)
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def migrate_players_from_txt(cursor):
    """Migrate players from players.txt to the database"""
    
    if not os.path.exists('players.txt'):
        print("ℹ️ players.txt not found, skipping migration")
        return
    
    try:
        with open('players.txt', 'r') as f:
            players = [line.strip() for line in f if line.strip()]
        
        migrated_count = 0
        for player_name in players:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO players (name, email) 
                    VALUES (?, ?)
                ''', (player_name, None))
                
                if cursor.rowcount > 0:
                    migrated_count += 1
                    
            except Exception as e:
                print(f"⚠️ Error migrating player {player_name}: {e}")
        
        print(f"✅ Migrated {migrated_count} players from players.txt")
        
        # Show current players in database
        cursor.execute("SELECT name, email FROM players ORDER BY name")
        db_players = cursor.fetchall()
        print(f"📊 Total players in database: {len(db_players)}")
        
    except Exception as e:
        print(f"❌ Error migrating players: {e}")

if __name__ == "__main__":
    print("🔧 Setting up schedule tables...")
    setup_schedule_tables()
