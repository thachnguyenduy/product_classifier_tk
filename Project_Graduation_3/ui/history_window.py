# ============================================
# HISTORY WINDOW - View Past Inspections
# ============================================

import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk


class HistoryWindow:
    """
    Window to view inspection history
    """
    
    def __init__(self, parent, database):
        self.database = database
        
        # Create top-level window
        self.window = tk.Toplevel(parent)
        self.window.title("Inspection History")
        self.window.geometry("900x600")
        
        self._build_ui()
        self._load_data()
    
    def _build_ui(self):
        """Build UI"""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title = ttk.Label(main_frame, text="📊 Inspection History", 
                          font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # Treeview for table
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create treeview
        self.tree = ttk.Treeview(tree_frame, 
                                  columns=("Time", "Result", "Reason", "Image"),
                                  show="headings",
                                  yscrollcommand=vsb.set,
                                  xscrollcommand=hsb.set)
        
        self.tree.heading("Time", text="Timestamp")
        self.tree.heading("Result", text="Result")
        self.tree.heading("Reason", text="Reason")
        self.tree.heading("Image", text="Image Path")
        
        self.tree.column("Time", width=150)
        self.tree.column("Result", width=80)
        self.tree.column("Reason", width=200)
        self.tree.column("Image", width=300)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        refresh_btn = ttk.Button(btn_frame, text="🔄 Refresh", command=self._load_data)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = ttk.Button(btn_frame, text="Close", command=self.window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)
    
    def _load_data(self):
        """Load data from database"""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get history
        history = self.database.get_history(limit=100)
        
        # Populate tree
        for row in history:
            timestamp, result, reason, image_path = row
            
            # Add with color tag
            tag = "ok" if result == 'O' else "ng"
            self.tree.insert("", tk.END, values=(timestamp, result, reason, image_path), tags=(tag,))
        
        # Configure tags
        self.tree.tag_configure("ok", background="#d4edda")
        self.tree.tag_configure("ng", background="#f8d7da")

