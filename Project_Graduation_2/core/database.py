"""
Database Handler for Coca-Cola Sorting System
Manages SQLite database for inspection history and statistics
"""

import sqlite3
import os
from datetime import datetime
import threading


class Database:
    """
    SQLite database handler for product inspection records
    Thread-safe implementation for concurrent access
    """
    
    def __init__(self, db_path="database/product.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.Lock()
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        print(f"[Database] Initialized at {db_path}")
    
    def _init_database(self):
        """Create tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create inspection records table
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
                    processing_time REAL
                )
            ''')
            
            # Create statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    total_count INTEGER DEFAULT 0,
                    ok_count INTEGER DEFAULT 0,
                    ng_count INTEGER DEFAULT 0,
                    UNIQUE(date)
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON inspections(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_result 
                ON inspections(result)
            ''')
            
            conn.commit()
            conn.close()
            
            print("[Database] Tables initialized")
            
        except Exception as e:
            print(f"[ERROR] Database initialization failed: {e}")
    
    def add_inspection(self, result_data):
        """
        Add inspection record to database
        
        Args:
            result_data: Dictionary containing:
                - result: 'OK' or 'NG'
                - reason: Explanation string
                - has_cap: bool
                - has_filled: bool
                - has_label: bool
                - defects_found: list of defect names
                - image_path: Path to saved image (optional)
                - processing_time: Time taken for inspection (optional)
        
        Returns:
            int: Record ID, or None if failed
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                cursor.execute('''
                    INSERT INTO inspections 
                    (timestamp, result, reason, has_cap, has_filled, has_label, 
                     defects, image_path, processing_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    result_data.get('result', 'UNKNOWN'),
                    result_data.get('reason', ''),
                    int(result_data.get('has_cap', False)),
                    int(result_data.get('has_filled', False)),
                    int(result_data.get('has_label', False)),
                    ', '.join(result_data.get('defects_found', [])),
                    result_data.get('image_path', ''),
                    result_data.get('processing_time', 0.0)
                ))
                
                record_id = cursor.lastrowid
                
                # Update daily statistics
                self._update_statistics(cursor, result_data.get('result', 'UNKNOWN'))
                
                conn.commit()
                conn.close()
                
                return record_id
                
        except Exception as e:
            print(f"[ERROR] Failed to add inspection record: {e}")
            return None
    
    def _update_statistics(self, cursor, result):
        """Update daily statistics (internal method)"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Insert or update statistics
        cursor.execute('''
            INSERT INTO statistics (date, total_count, ok_count, ng_count)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                total_count = total_count + 1,
                ok_count = ok_count + ?,
                ng_count = ng_count + ?
        ''', (
            today,
            1 if result == 'OK' else 0,
            1 if result == 'NG' else 0,
            1 if result == 'OK' else 0,
            1 if result == 'NG' else 0
        ))
    
    def get_recent_inspections(self, limit=100):
        """
        Get recent inspection records
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            list: List of inspection records (dicts)
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM inspections 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                
                # Convert to list of dicts
                records = []
                for row in rows:
                    records.append({
                        'id': row['id'],
                        'timestamp': row['timestamp'],
                        'result': row['result'],
                        'reason': row['reason'],
                        'has_cap': bool(row['has_cap']),
                        'has_filled': bool(row['has_filled']),
                        'has_label': bool(row['has_label']),
                        'defects': row['defects'],
                        'image_path': row['image_path'],
                        'processing_time': row['processing_time']
                    })
                
                conn.close()
                
                return records
                
        except Exception as e:
            print(f"[ERROR] Failed to get recent inspections: {e}")
            return []
    
    def get_statistics(self, days=7):
        """
        Get statistics for the last N days
        
        Args:
            days: Number of days to include
        
        Returns:
            dict: Statistics summary
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get today's statistics
                today = datetime.now().strftime("%Y-%m-%d")
                cursor.execute('''
                    SELECT total_count, ok_count, ng_count 
                    FROM statistics 
                    WHERE date = ?
                ''', (today,))
                
                row = cursor.fetchone()
                today_stats = {
                    'total': row[0] if row else 0,
                    'ok': row[1] if row else 0,
                    'ng': row[2] if row else 0
                }
                
                # Get all-time statistics
                cursor.execute('''
                    SELECT 
                        SUM(total_count) as total,
                        SUM(ok_count) as ok,
                        SUM(ng_count) as ng
                    FROM statistics
                ''')
                
                row = cursor.fetchone()
                all_time_stats = {
                    'total': row[0] if row[0] else 0,
                    'ok': row[1] if row[1] else 0,
                    'ng': row[2] if row[2] else 0
                }
                
                # Calculate percentages
                if all_time_stats['total'] > 0:
                    all_time_stats['ok_rate'] = (all_time_stats['ok'] / all_time_stats['total']) * 100
                    all_time_stats['ng_rate'] = (all_time_stats['ng'] / all_time_stats['total']) * 100
                else:
                    all_time_stats['ok_rate'] = 0
                    all_time_stats['ng_rate'] = 0
                
                if today_stats['total'] > 0:
                    today_stats['ok_rate'] = (today_stats['ok'] / today_stats['total']) * 100
                    today_stats['ng_rate'] = (today_stats['ng'] / today_stats['total']) * 100
                else:
                    today_stats['ok_rate'] = 0
                    today_stats['ng_rate'] = 0
                
                conn.close()
                
                return {
                    'today': today_stats,
                    'all_time': all_time_stats
                }
                
        except Exception as e:
            print(f"[ERROR] Failed to get statistics: {e}")
            return {
                'today': {'total': 0, 'ok': 0, 'ng': 0, 'ok_rate': 0, 'ng_rate': 0},
                'all_time': {'total': 0, 'ok': 0, 'ng': 0, 'ok_rate': 0, 'ng_rate': 0}
            }
    
    def clear_history(self):
        """Clear all inspection records (keep statistics)"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM inspections')
                
                conn.commit()
                conn.close()
                
                print("[Database] History cleared")
                return True
                
        except Exception as e:
            print(f"[ERROR] Failed to clear history: {e}")
            return False
    
    def get_defect_summary(self):
        """
        Get summary of defect types
        
        Returns:
            dict: Defect counts
        """
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT defects FROM inspections 
                    WHERE result = 'NG' AND defects != ''
                ''')
                
                rows = cursor.fetchall()
                
                # Count defect types
                defect_counts = {
                    'Cap-Defect': 0,
                    'Filling-Defect': 0,
                    'Label-Defect': 0,
                    'Wrong-Product': 0,
                    'Missing-Components': 0
                }
                
                for row in rows:
                    defects = row[0]
                    if 'Cap-Defect' in defects:
                        defect_counts['Cap-Defect'] += 1
                    if 'Filling-Defect' in defects:
                        defect_counts['Filling-Defect'] += 1
                    if 'Label-Defect' in defects:
                        defect_counts['Label-Defect'] += 1
                    if 'Wrong-Product' in defects:
                        defect_counts['Wrong-Product'] += 1
                    if 'Missing' in defects:
                        defect_counts['Missing-Components'] += 1
                
                conn.close()
                
                return defect_counts
                
        except Exception as e:
            print(f"[ERROR] Failed to get defect summary: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        print("[Database] Closed")

