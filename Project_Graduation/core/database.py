"""
Database Handler for Coca-Cola Sorting System
SQLite database for logging inspection results and statistics
"""

import sqlite3
import threading
from datetime import datetime
from pathlib import Path


class Database:
    """
    SQLite database handler for inspection logging
    """
    
    def __init__(self, db_path="database/product.db"):
        """
        Initialize database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.Lock()
        
        # Create database directory if needed
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        print(f"[Database] Initialized at {db_path}")

    def _connect(self):
        """
        Create a new SQLite connection.
        Using a small timeout helps avoid hard freezes when the DB is temporarily locked.
        """
        return sqlite3.connect(self.db_path, timeout=3.0)
    
    def _init_database(self):
        """Create tables if they don't exist"""
        with self.lock:
            with self._connect() as conn:
                cursor = conn.cursor()

                # Improve concurrency on SQLite (helps UI reads while background writes)
                try:
                    cursor.execute("PRAGMA journal_mode=WAL;")
                except Exception:
                    # Some environments may not support WAL; safe to ignore
                    pass

                # Inspections table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS inspections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        result TEXT NOT NULL,
                        reason TEXT,
                        has_cap INTEGER,
                        has_filled INTEGER,
                        has_label INTEGER,
                        defects TEXT,
                        image_path TEXT,
                        processing_time REAL,
                        num_detections INTEGER
                    )
                ''')

                # Statistics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS statistics (
                        date TEXT PRIMARY KEY,
                        total_count INTEGER DEFAULT 0,
                        ok_count INTEGER DEFAULT 0,
                        ng_count INTEGER DEFAULT 0
                    )
                ''')

                # If user already has an older DB file, it may be missing newer columns.
                # Auto-migrate to keep the app working without deleting the DB.
                self._migrate_schema(cursor)

    def _migrate_schema(self, cursor):
        """
        Ensure required columns exist (handles upgrading old DBs).
        This is critical on Windows where users often keep the same product.db across versions.
        """
        def ensure_column(table, col_name, col_type):
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                existing = {row[1] for row in cursor.fetchall()}  # row[1] = column name
                if col_name not in existing:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                    print(f"[Database] Migrated: added {table}.{col_name} ({col_type})")
            except Exception as e:
                print(f"[Database] Migration warning for {table}.{col_name}: {e}")

        # inspections columns (newer versions might add more over time)
        ensure_column("inspections", "reason", "TEXT")
        ensure_column("inspections", "has_cap", "INTEGER")
        ensure_column("inspections", "has_filled", "INTEGER")
        ensure_column("inspections", "has_label", "INTEGER")
        ensure_column("inspections", "defects", "TEXT")
        ensure_column("inspections", "image_path", "TEXT")
        ensure_column("inspections", "processing_time", "REAL")
        ensure_column("inspections", "num_detections", "INTEGER")

        # statistics columns
        ensure_column("statistics", "total_count", "INTEGER DEFAULT 0")
        ensure_column("statistics", "ok_count", "INTEGER DEFAULT 0")
        ensure_column("statistics", "ng_count", "INTEGER DEFAULT 0")
    
    def add_inspection(self, result_dict):
        """
        Add inspection result to database
        
        Args:
            result_dict: Dictionary with inspection results
                - result: 'OK' or 'NG'
                - reason: Explanation string
                - has_cap: Boolean
                - has_filled: Boolean
                - has_label: Boolean
                - defects_found: List of defect names
                - image_path: Path to saved image
                - processing_time: Time in seconds
                - detections: List of detections
        """
        with self.lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()

                    # Extract data
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    result = result_dict.get('result', 'UNKNOWN')
                    reason = result_dict.get('reason', '')
                    has_cap = 1 if result_dict.get('has_cap', False) else 0
                    has_filled = 1 if result_dict.get('has_filled', False) else 0
                    has_label = 1 if result_dict.get('has_label', False) else 0
                    defects = ', '.join(result_dict.get('defects_found', []))
                    image_path = result_dict.get('image_path', '')
                    processing_time = result_dict.get('processing_time', 0.0)
                    num_detections = len(result_dict.get('detections', []))

                    # Insert inspection
                    cursor.execute('''
                        INSERT INTO inspections 
                        (timestamp, result, reason, has_cap, has_filled, has_label,
                         defects, image_path, processing_time, num_detections)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (timestamp, result, reason, has_cap, has_filled, has_label,
                          defects, image_path, processing_time, num_detections))

                    # Update statistics
                    date = datetime.now().strftime("%Y-%m-%d")

                    cursor.execute('SELECT total_count, ok_count, ng_count FROM statistics WHERE date = ?', (date,))
                    row = cursor.fetchone()

                    if row:
                        if result == 'OK':
                            cursor.execute('''
                                UPDATE statistics 
                                SET total_count = total_count + 1,
                                    ok_count = ok_count + 1
                                WHERE date = ?
                            ''', (date,))
                        else:
                            cursor.execute('''
                                UPDATE statistics 
                                SET total_count = total_count + 1,
                                    ng_count = ng_count + 1
                                WHERE date = ?
                            ''', (date,))
                    else:
                        if result == 'OK':
                            cursor.execute('''
                                INSERT INTO statistics (date, total_count, ok_count, ng_count)
                                VALUES (?, 1, 1, 0)
                            ''', (date,))
                        else:
                            cursor.execute('''
                                INSERT INTO statistics (date, total_count, ok_count, ng_count)
                                VALUES (?, 1, 0, 1)
                            ''', (date,))
            except Exception as e:
                print(f"[ERROR] Failed to add inspection to database: {e}")
    
    def get_recent_inspections(self, limit=100):
        """
        Get recent inspection records
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of tuples (inspection data)
        """
        with self.lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT * FROM inspections 
                        ORDER BY id DESC 
                        LIMIT ?
                    ''', (limit,))
                    return cursor.fetchall()
            except Exception as e:
                print(f"[ERROR] Failed to get inspections: {e}")
                return []
    
    def get_statistics(self, days=7):
        """
        Get statistics for recent days
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of tuples (date, total, ok, ng)
        """
        with self.lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT * FROM statistics 
                        ORDER BY date DESC 
                        LIMIT ?
                    ''', (days,))
                    return cursor.fetchall()
            except Exception as e:
                print(f"[ERROR] Failed to get statistics: {e}")
                return []
    
    def get_today_statistics(self):
        """
        Get today's statistics
        
        Returns:
            dict with keys: total, ok, ng, pass_rate
        """
        with self.lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    date = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute('''
                        SELECT total_count, ok_count, ng_count 
                        FROM statistics 
                        WHERE date = ?
                    ''', (date,))
                    row = cursor.fetchone()

                if row:
                    total, ok, ng = row
                    pass_rate = (ok / total * 100) if total > 0 else 0
                    return {'total': total, 'ok': ok, 'ng': ng, 'pass_rate': pass_rate}

                return {'total': 0, 'ok': 0, 'ng': 0, 'pass_rate': 0}
            except Exception as e:
                print(f"[ERROR] Failed to get today's statistics: {e}")
                return {'total': 0, 'ok': 0, 'ng': 0, 'pass_rate': 0}
    
    def clear_old_records(self, days=30):
        """
        Delete records older than specified days
        
        Args:
            days: Keep records from last N days
        """
        with self.lock:
            try:
                with self._connect() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        DELETE FROM inspections 
                        WHERE timestamp < datetime('now', '-' || ? || ' days')
                    ''', (days,))
                    deleted = cursor.rowcount
                print(f"[Database] Deleted {deleted} old records")
            except Exception as e:
                print(f"[ERROR] Failed to clear old records: {e}")
