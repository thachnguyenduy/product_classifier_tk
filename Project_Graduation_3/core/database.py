# ============================================
# DATABASE MODULE - SQLite Handler
# ============================================

import sqlite3
import os
from datetime import datetime
import config


class Database:
    """
    SQLite database for logging inspection results
    """
    
    def __init__(self):
        self.db_path = config.DB_PATH
        
        # Create directory if needed
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self._create_tables()
        print(f"[Database] Initialized: {self.db_path}")
    
    def _create_tables(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Inspections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                result TEXT NOT NULL,
                reason TEXT,
                has_cap INTEGER,
                has_filled INTEGER,
                has_label INTEGER,
                has_defects INTEGER,
                defects TEXT,
                image_path TEXT,
                processing_time REAL
            )
        """)
        
        # Statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_count INTEGER DEFAULT 0,
                ok_count INTEGER DEFAULT 0,
                ng_count INTEGER DEFAULT 0,
                avg_processing_time REAL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_inspection(self, data):
        """
        Add inspection record
        
        Args:
            data: dict with inspection details
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO inspections 
            (timestamp, result, reason, has_cap, has_filled, has_label, has_defects, defects, image_path, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            data.get('result', 'O'),
            data.get('reason', ''),
            int(data.get('has_cap', False)),
            int(data.get('has_filled', False)),
            int(data.get('has_label', False)),
            int(data.get('has_defects', False)),
            ','.join(data.get('defects_found', [])),
            data.get('image_path', ''),
            data.get('processing_time_ms', 0) / 1000.0
        ))
        
        # Update statistics
        today = datetime.now().strftime("%Y-%m-%d")
        self._update_statistics(cursor, today, data.get('result', 'O'))
        
        conn.commit()
        conn.close()
    
    def _update_statistics(self, cursor, date, result):
        """Update daily statistics"""
        # Check if record exists
        cursor.execute("SELECT * FROM statistics WHERE date = ?", (date,))
        row = cursor.fetchone()
        
        if row is None:
            # Create new record
            cursor.execute("""
                INSERT INTO statistics (date, total_count, ok_count, ng_count)
                VALUES (?, 1, ?, ?)
            """, (date, 1 if result == 'O' else 0, 1 if result == 'N' else 0))
        else:
            # Update existing
            cursor.execute("""
                UPDATE statistics
                SET total_count = total_count + 1,
                    ok_count = ok_count + ?,
                    ng_count = ng_count + ?
                WHERE date = ?
            """, (1 if result == 'O' else 0, 1 if result == 'N' else 0, date))
    
    def get_history(self, limit=100):
        """Get recent inspection history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, result, reason, image_path
            FROM inspections
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    
    def get_statistics(self, days=7):
        """Get statistics for recent days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT date, total_count, ok_count, ng_count
            FROM statistics
            ORDER BY date DESC
            LIMIT ?
        """, (days,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows

