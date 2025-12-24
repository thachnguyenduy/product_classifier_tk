"""
History Window for Coca-Cola Sorting System
Display inspection history and statistics
"""

import tkinter as tk
from tkinter import ttk
import threading


class HistoryWindow:
    """
    Window for viewing inspection history
    """
    
    def __init__(self, parent, database):
        """
        Initialize history window
        
        Args:
            parent: Parent window
            database: Database object
        """
        self.database = database
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Inspection History")
        self.window.geometry("1000x600")
        self.window.configure(bg='#2c3e50')
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
        
        self._setup_ui()
        self._load_data_async()
    
    def _setup_ui(self):
        """Setup UI layout"""
        # Title
        title_label = tk.Label(self.window, text="INSPECTION HISTORY",
                              font=('Arial', 16, 'bold'),
                              bg='#2c3e50', fg='white')
        title_label.pack(pady=10)
        
        # Frame for table
        table_frame = tk.Frame(self.window, bg='#34495e')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        
        # Treeview (table)
        columns = ('ID', 'Time', 'Result', 'Reason', 'Cap', 'Filled', 'Label', 'Defects', 'Time(ms)')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                yscrollcommand=v_scrollbar.set,
                                xscrollcommand=h_scrollbar.set)
        
        # Configure scrollbars
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        # Column headings
        self.tree.heading('ID', text='ID')
        self.tree.heading('Time', text='Timestamp')
        self.tree.heading('Result', text='Result')
        self.tree.heading('Reason', text='Reason')
        self.tree.heading('Cap', text='Cap')
        self.tree.heading('Filled', text='Filled')
        self.tree.heading('Label', text='Label')
        self.tree.heading('Defects', text='Defects')
        self.tree.heading('Time(ms)', text='Time(ms)')
        
        # Column widths
        self.tree.column('ID', width=50)
        self.tree.column('Time', width=150)
        self.tree.column('Result', width=60)
        self.tree.column('Reason', width=200)
        self.tree.column('Cap', width=50)
        self.tree.column('Filled', width=60)
        self.tree.column('Label', width=60)
        self.tree.column('Defects', width=150)
        self.tree.column('Time(ms)', width=80)
        
        # Pack elements
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = tk.Frame(self.window, bg='#2c3e50')
        button_frame.pack(pady=10)
        
        self.refresh_btn = tk.Button(
            button_frame, text="REFRESH",
            font=('Arial', 11),
            bg='#3498db', fg='white',
            width=15,
            command=self._load_data_async
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(
            button_frame, text="CLOSE",
            font=('Arial', 11),
            bg='#95a5a6', fg='white',
            width=15,
            command=self.window.destroy
        )
        close_btn.pack(side=tk.LEFT, padx=5)
    
    def _load_data_async(self):
        """
        Load inspection data from database without blocking the Tkinter UI thread.
        This prevents REFRESH/CLOSE from "freezing" when the DB is temporarily locked.
        """
        try:
            if hasattr(self, "refresh_btn") and self.refresh_btn:
                self.refresh_btn.configure(state=tk.DISABLED, text="LOADING...")
        except Exception:
            pass

        t = threading.Thread(target=self._fetch_and_render, daemon=True)
        t.start()

    def _fetch_and_render(self):
        try:
            inspections = self.database.get_recent_inspections(limit=100)
        except Exception:
            inspections = []

        # Render on UI thread
        self.window.after(0, self._render_rows, inspections)

    def _render_rows(self, inspections):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in inspections:
            # row format: (id, timestamp, result, reason, has_cap, has_filled,
            #              has_label, defects, image_path, processing_time, num_detections)
            id_val = row[0]
            timestamp = row[1]
            result = row[2]
            reason = row[3]
            has_cap = '✓' if row[4] else '✗'
            has_filled = '✓' if row[5] else '✗'
            has_label = '✓' if row[6] else '✗'
            defects = row[7] if row[7] else '-'
            proc_time = f"{row[9]*1000:.1f}" if row[9] else '-'

            item_id = self.tree.insert('', tk.END, values=(
                id_val, timestamp, result, reason,
                has_cap, has_filled, has_label, defects, proc_time
            ))

            self.tree.item(item_id, tags=('ok',) if result == 'OK' else ('ng',))

        # Configure tags
        self.tree.tag_configure('ok', background='#d5f4e6')
        self.tree.tag_configure('ng', background='#fadbd8')

        try:
            if hasattr(self, "refresh_btn") and self.refresh_btn:
                self.refresh_btn.configure(state=tk.NORMAL, text="REFRESH")
        except Exception:
            pass
