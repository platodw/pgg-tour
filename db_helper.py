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
    
    def execute(self, query, params=None):
        """Execute query, converting ? placeholders to %s for Postgres"""
        if params is not None:
            # Convert SQLite ? placeholders to Postgres %s placeholders
            query = query.replace('?', '%s')
        return self._cursor.execute(query, params)
    
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
    
    def cursor(self):
        """Return a wrapped cursor that converts ? to %s automatically"""
        return PostgresCursor(self._conn.cursor())
    
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

