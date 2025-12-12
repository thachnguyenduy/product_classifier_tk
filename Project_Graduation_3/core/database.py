# ============================================
# DATABASE MODULE - SQLite Handler
# ============================================
"""
Database for logging inspection results

Schema:
- inspections: Individual bottle inspection records
- statistics: Daily statistics

Each inspection includes:
- Timestamp
- Object ID (tracking ID)
- Detected labels (comma-separated)
- Final result (OK / NG)
- Reason
- Image path
"""

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
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Inspections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                object_id INTEGER,
                detected_labels TEXT,
                result TEXT NOT NULL,
                reason TEXT,
                image_path TEXT,
                processing_time REAL
            )
        """)
        
        # Statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_count INTEGER DEFAULT 0,
                ok_count INTEGER DEFAULT 0,
                ng_count INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
        print("[Database] Tables created/verified")
    
    def add_inspection(self, data):
        """
        Add inspection record
        
        Args:
            data: dict with keys:
                - object_id: Tracking ID
                - detected_labels: set or list of class names
                - result: 'OK' or 'NG'
                - reason: Reason string
                - image_path: Path to saved image
                - processing_time: Time in milliseconds (optional)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert detected_labels to comma-separated string
        detected_labels = data.get('detected_labels', set())
        if isinstance(detected_labels, set):
            labels_str = ', '.join(sorted(detected_labels))
        elif isinstance(detected_labels, list):
            labels_str = ', '.join(detected_labels)
        else:
            labels_str = str(detected_labels)
        
        cursor.execute("""
            INSERT INTO inspections 
            (timestamp, object_id, detected_labels, result, reason, image_path, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            data.get('object_id', None),
            labels_str,
            data.get('result', 'NG'),
            data.get('reason', ''),
            data.get('image_path', ''),
            data.get('processing_time', 0) / 1000.0  # Convert ms to seconds
        ))
        
        # Update statistics
        today = datetime.now().strftime("%Y-%m-%d")
        self._update_statistics(cursor, today, data.get('result', 'NG'))
        
        conn.commit()
        conn.close()
        
        if config.VERBOSE_LOGGING:
            print(f"[Database] Added inspection: {data.get('result')} | {data.get('reason')}")
    
    def _update_statistics(self, cursor, date, result):
        """Update daily statistics"""
        # Try to update existing record
        cursor.execute("""
            UPDATE statistics
            SET total_count = total_count + 1,
                ok_count = ok_count + ?,
                ng_count = ng_count + ?
            WHERE date = ?
        """, (
            1 if result == 'OK' else 0,
            1 if result == 'NG' else 0,
            date
        ))
        
        # If no row was updated, insert new record
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO statistics (date, total_count, ok_count, ng_count)
                VALUES (?, 1, ?, ?)
            """, (
                date,
                1 if result == 'OK' else 0,
                1 if result == 'NG' else 0
            ))
    
    def get_history(self, limit=100):
        """
        Get recent inspection history
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of tuples: (timestamp, object_id, detected_labels, result, reason, image_path)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, object_id, detected_labels, result, reason, image_path
            FROM inspections
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    
    def get_statistics(self, days=7):
        """
        Get statistics for recent days
        
        Args:
            days: Number of days to retrieve
        
        Returns:
            List of tuples: (date, total_count, ok_count, ng_count)
        """
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
    
    def get_today_stats(self):
        """
        Get today's statistics
        
        Returns:
            dict: {'total': int, 'ok': int, 'ng': int} or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute("""
            SELECT total_count, ok_count, ng_count
            FROM statistics
            WHERE date = ?
        """, (today,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'total': row[0],
                'ok': row[1],
                'ng': row[2]
            }
        else:
            return {'total': 0, 'ok': 0, 'ng': 0}
    
    def clear_history(self):
        """Clear all inspection history (use with caution!)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM inspections")
        cursor.execute("DELETE FROM statistics")
        
        conn.commit()
        conn.close()
        
        print("[Database] History cleared")
