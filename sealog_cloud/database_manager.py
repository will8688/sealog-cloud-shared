import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import re
import streamlit as st

class DatabaseManager:
    """
    Database abstraction layer that handles both SQLite and PostgreSQL
    Prepares for future offline/online mode switching
    """
    
    def __init__(self):
        self.db_type = self._determine_database_type()
        self.connection_params = self._get_connection_params()
        self._engine = None
    
    def _determine_database_type(self) -> str:
        """Determine which database to use based on environment and user settings"""
        # Check if we're in production (Railway) or development
        if os.getenv('DATABASE_URL'):
            return 'postgresql'
        
        # Check user preference for offline mode (future feature)
        if hasattr(st.session_state, 'use_offline_mode') and st.session_state.use_offline_mode:
            return 'sqlite'
        
        
        return 'postgresql'
    
    def _get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters based on database type"""
        if self.db_type == 'postgresql':
            return {
                'database_url': os.getenv('DATABASE_URL', 'postgresql://postgres:qZSyDZAgjfOIiDNsVxVlCKfPfnCCkhPU@crossover.proxy.rlwy.net:57261/railway'),
                'host': 'crossover.proxy.rlwy.net',
                'port': 57261,
                'user': 'postgres',
                'password': 'qZSyDZAgjfOIiDNsVxVlCKfPfnCCkhPU',
                'database': 'railway',
                'sslmode': 'require'
            }
        else:  # sqlite
            return {
                'database_path': 'sea_log.db'
            }
    
    @property
    def engine(self):
        """Get SQLAlchemy engine (lazy loading)"""
        if self._engine is None:
            if self.db_type == 'postgresql':
                self._engine = create_engine(self.connection_params['database_url'])
            else:
                self._engine = create_engine(f"sqlite:///{self.connection_params['database_path']}")
        return self._engine
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            if self.db_type == 'postgresql':
                conn = psycopg2.connect(**{k: v for k, v in self.connection_params.items() if k != 'database_url'})
                yield conn
            else:
                conn = sqlite3.connect(self.connection_params['database_path'], check_same_thread=False)
                conn.execute("PRAGMA foreign_keys = ON")
                yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursors"""
        with self.get_connection() as conn:
            if self.db_type == 'postgresql':
                cursor = conn.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = conn.cursor()
                # Make SQLite return dict-like rows
                cursor.row_factory = sqlite3.Row
            
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = (), fetch: str = None) -> Union[List[Dict], Dict, None]:
            """
            Execute a query with automatic parameter binding for both databases
            
            Args:
                query: SQL query string
                params: Query parameters
                fetch: 'one', 'all', or None
            
            Returns:
                Query results or None
            """
            # Convert SQLite ? placeholders to PostgreSQL %s placeholders
            if self.db_type == 'postgresql' and '?' in query:
                query = query.replace('?', '%s')
            
            # Convert boolean comparisons for PostgreSQL compatibility
            if self.db_type == 'postgresql':
                # Replace common boolean patterns with proper PostgreSQL boolean values
                boolean_replacements = {
                    'is_active = 1': 'is_active = TRUE',
                    'is_active = 0': 'is_active = FALSE',
                    'is_expired = 1': 'is_expired = TRUE',
                    'is_expired = 0': 'is_expired = FALSE',
                    'is_accepted = 1': 'is_accepted = TRUE',
                    'is_accepted = 0': 'is_accepted = FALSE',
                    'can_make_entries = 1': 'can_make_entries = TRUE',
                    'can_make_entries = 0': 'can_make_entries = FALSE',
                    'is_default = 1': 'is_default = TRUE',
                    'is_default = 0': 'is_default = FALSE',
                    'is_current = 1': 'is_current = TRUE',
                    'is_current = 0': 'is_current = FALSE',
                    'verified = 1': 'verified = TRUE',
                    'verified = 0': 'verified = FALSE',
                    # Handle cases without spaces
                    'is_active=1': 'is_active=TRUE',
                    'is_active=0': 'is_active=FALSE',
                    'is_expired=1': 'is_expired=TRUE',
                    'is_expired=0': 'is_expired=FALSE',
                    'is_accepted=1': 'is_accepted=TRUE',
                    'is_accepted=0': 'is_accepted=FALSE',
                    'verified=1': 'verified=TRUE',
                    'verified=0': 'verified=FALSE',
                }
                
                for sqlite_pattern, postgres_pattern in boolean_replacements.items():
                    query = query.replace(sqlite_pattern, postgres_pattern)
                
                # Handle user_id data type casting (convert integer to string for VARCHAR columns)
                # This fixes "character varying = integer" errors
                query = re.sub(r'\buser_id\s*=\s*(\d+)', r"user_id = '\1'", query)
                query = re.sub(r'\bvessel_id\s*=\s*(\d+)', r"vessel_id = '\1'", query) 
                query = re.sub(r'\bcrew_member_id\s*=\s*(\d+)', r"crew_member_id = '\1'", query)
                query = re.sub(r'\blog_period_id\s*=\s*(\d+)', r"log_period_id = '\1'", query)
                
                # Handle WHERE clauses with integers
                query = re.sub(r'WHERE\s+user_id\s*=\s*(\d+)', r"WHERE user_id = '\1'", query)
                query = re.sub(r'WHERE\s+vessel_id\s*=\s*(\d+)', r"WHERE vessel_id = '\1'", query)
                
                # Handle parameters in queries - FIXED VERSION
                # Only convert the first parameter if it's an integer and the query starts with typical ID-based patterns
                if params:
                    converted_params = []
                    for i, param in enumerate(params):
                        # Only convert the first parameter if it's likely a user_id/vessel_id/etc
                        # and the query pattern suggests it's an ID parameter
                        if (i == 0 and isinstance(param, int) and 
                            (query.startswith('SELECT') or query.startswith('UPDATE') or query.startswith('DELETE')) and
                            ('WHERE user_id =' in query or 'WHERE vessel_id =' in query or 
                             'WHERE crew_member_id =' in query or 'WHERE log_period_id =' in query or
                             'user_id =' in query.split('WHERE')[0] if 'WHERE' in query else False)):
                            converted_params.append(str(param))
                        else:
                            # Keep all other parameters (including dates) as-is
                            converted_params.append(param)
                    params = tuple(converted_params)
            
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch == 'one':
                    result = cursor.fetchone()
                    return dict(result) if result else None
                elif fetch == 'all':
                    results = cursor.fetchall()
                    return [dict(row) for row in results] if results else []
                else:
                    return None
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute many queries with parameter lists"""
        if self.db_type == 'postgresql' and '?' in query:
            query = query.replace('?', '%s')
        
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        if self.db_type == 'postgresql':
            query = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """
            result = self.execute_query(query, (table_name,), fetch='one')
            return result['exists'] if result else False
        else:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, (table_name,), fetch='one')
            return result is not None
    
    def get_table_schema(self, table_name: str) -> List[Dict]:
        """Get table schema information"""
        if self.db_type == 'postgresql':
            query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """
        else:
            query = f"PRAGMA table_info({table_name})"
        
        return self.execute_query(query, (table_name,), fetch='all')
    
    def create_table_from_schema(self, table_name: str, schema_sql: str) -> None:
        """Create table using schema SQL"""
        # Convert SQLite schema to PostgreSQL if needed
        if self.db_type == 'postgresql':
            schema_sql = self._convert_sqlite_to_postgresql_schema(schema_sql)
        
        self.execute_query(schema_sql)
    
    def _convert_sqlite_to_postgresql_schema(self, sqlite_schema: str) -> str:
        """Convert SQLite schema to PostgreSQL schema"""
        # Basic conversions
        conversions = {
            'INTEGER PRIMARY KEY AUTOINCREMENT': 'SERIAL PRIMARY KEY',
            'INTEGER PRIMARY KEY': 'SERIAL PRIMARY KEY', 
            'TEXT': 'VARCHAR',
            'REAL': 'NUMERIC',
            'BLOB': 'BYTEA',
            'TIMESTAMP DEFAULT CURRENT_TIMESTAMP': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            'datetime(\'now\')': 'CURRENT_TIMESTAMP'
        }
        
        postgresql_schema = sqlite_schema
        for sqlite_type, postgres_type in conversions.items():
            postgresql_schema = postgresql_schema.replace(sqlite_type, postgres_type)
        
        return postgresql_schema
    
    def get_all_table_names(self) -> List[str]:
        """Get all table names in the database"""
        if self.db_type == 'postgresql':
            query = """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
        else:
            query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        
        results = self.execute_query(query, fetch='all')
        if self.db_type == 'postgresql':
            return [row['table_name'] for row in results]
        else:
            return [row['name'] for row in results]
    
    def test_connection(self) -> tuple[bool, str]:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                if self.db_type == 'postgresql':
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT version()")
                        version = cursor.fetchone()[0]
                        return True, f"Connected to PostgreSQL: {version}"
                else:
                    cursor = conn.cursor()
                    cursor.execute("SELECT sqlite_version()")
                    version = cursor.fetchone()[0]
                    return True, f"Connected to SQLite: {version}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def switch_database_mode(self, use_offline: bool = False) -> None:
        """Switch between online (PostgreSQL) and offline (SQLite) modes"""
        st.session_state.use_offline_mode = use_offline
        self.db_type = self._determine_database_type()
        self.connection_params = self._get_connection_params()
        self._engine = None  # Reset engine to recreate with new settings

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions for backward compatibility
def get_database_connection():
    """Get database connection (backward compatibility)"""
    return db_manager.get_connection()

def get_cursor():
    """Get database cursor (backward compatibility)"""
    return db_manager.get_cursor()

def execute_query(query: str, params: tuple = (), fetch: str = None) -> Union[List[Dict], Dict, None]:
    """
    Execute a query using the global database manager (backward compatibility)
    
    Args:
        query: SQL query string
        params: Query parameters
        fetch: 'one', 'all', or None
    
    Returns:
        Query results or None
    """
    return db_manager.execute_query(query, params, fetch)

def check_existing_table_types():
    """Check the data types of existing tables"""
    try:
        tables_to_check = ['users', 'vessels', 'log_periods']
        
        for table in tables_to_check:
            if db_manager.table_exists(table):
                print(f" DEBUG: Checking {table} table structure...")
                schema = db_manager.get_table_schema(table)
                for column in schema:
                    if 'id' in column.get('column_name', column.get('name', '')).lower():
                        print(f" DEBUG: {table}.{column.get('column_name', column.get('name', ''))} = {column.get('data_type', column.get('type', ''))}")
            else:
                print(f" DEBUG: Table {table} does not exist")
                
    except Exception as e:
        print(f" DEBUG: Error checking table types: {e}")