"""
Database helper module to handle both SQLite (local) and Postgres (production)
Provides a unified interface that works with both databases
"""
import os
import sqlite3

class PostgresCursor:
    """Wrapper for Postgres cursor to make it SQLite-compatible"""
    def __init__(self, cursor):
        self._cursor = cursor
        self._last_inserted_id = None
    
    def execute(self, query, params=None):
        """Execute query, converting SQLite syntax to Postgres syntax"""
        import re
        
        # Store original query for checking if it's an INSERT
        original_query = query
        
        # Convert SQLite ? placeholders to Postgres %s placeholders
        if params is not None:
            query = query.replace('?', '%s')
        
        # Convert SQLite-specific functions to Postgres equivalents
        # GROUP_CONCAT -> STRING_AGG (syntax is compatible)
        query = query.replace('GROUP_CONCAT', 'STRING_AGG')
        
        # date('now') -> CURRENT_DATE
        query = query.replace("date('now')", 'CURRENT_DATE')
        query = query.replace("date(\'now\')", 'CURRENT_DATE')
        
        # Handle INSERT queries to get last inserted ID for Postgres
        # Only add RETURNING for simple, single-line INSERT statements
        is_insert = re.match(r'^\s*INSERT\s+INTO', query.strip(), re.IGNORECASE | re.MULTILINE)
        if is_insert and 'RETURNING' not in query.upper():
            # Only add RETURNING for simple single-line INSERTs (no SELECT, VALUES only)
            if 'VALUES' in query.upper() and 'SELECT' not in query.upper():
                # Check if it's a simple VALUES insert (single line or simple multi-line)
                lines = query.strip().split('\n')
                if len(lines) <= 3:  # Simple INSERT with VALUES on one or two lines
                    # Add RETURNING id at the end, before semicolon if present
                    query = query.rstrip(';').rstrip() + ' RETURNING id'
        
        result = self._cursor.execute(query, params)
        
        # If INSERT with RETURNING, fetch the ID
        if 'RETURNING' in query.upper() and is_insert:
            try:
                row = self._cursor.fetchone()
                if row:
                    self._last_inserted_id = row[0]
            except Exception:
                # Some queries might not return a value
                pass
        
        return result
    
    @property
    def lastrowid(self):
        """Return last inserted row ID for Postgres compatibility"""
        # For Postgres, we need to check if we have a returning value
        # The PostgresConnection wrapper stores it after INSERT
        if hasattr(self, '_last_inserted_id'):
            return self._last_inserted_id
        return None
    
    @property
    def rowcount(self):
        """Return number of affected rows"""
        return self._cursor.rowcount
    
    def fetchone(self):
        return self._cursor.fetchone()
    
    def fetchall(self):
        return self._cursor.fetchall()
    
    def fetchmany(self, size=None):
        return self._cursor.fetchmany(size)
    
    def __getattr__(self, name):
        # Forward all other attributes to the real cursor
        return getattr(self._cursor, name)

class PostgresConnection:
    """Wrapper for Postgres connection to make it SQLite-compatible"""
    def __init__(self, conn):
        self._conn = conn
        self._last_inserted_id = None
    
    def cursor(self):
        """Return a wrapped cursor that converts ? to %s automatically"""
        cursor = PostgresCursor(self._conn.cursor())
        cursor._last_inserted_id = None  # Store last inserted ID
        return cursor
    
    def commit(self):
        return self._conn.commit()
    
    def rollback(self):
        return self._conn.rollback()
    
    def close(self):
        return self._conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()

def get_db():
    """
    Get database connection - uses Postgres on Heroku, SQLite locally
    Returns a connection object compatible with both SQLite and Postgres
    """
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Production: Use Postgres
        # Convert postgres:// to postgresql:// for psycopg2
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        try:
            import psycopg2
            pg_conn = psycopg2.connect(database_url)
            return PostgresConnection(pg_conn)
        except ImportError:
            print("⚠️ Warning: psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
        except Exception as e:
            print(f"❌ Error connecting to Postgres: {e}")
            raise
    else:
        # Development: Use SQLite
        return sqlite3.connect('golf_scores.db')

