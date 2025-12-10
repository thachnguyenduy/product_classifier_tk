"""
History Window for Coca-Cola Sorting System
Displays inspection history and statistics
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import os


class HistoryWindow:
    """
    History viewer window showing past inspections and statistics
    """
    
    def __init__(self, parent, database):
        """
        Initialize history window
        
        Args:
            parent: Parent Tkinter window
            database: Database instance
        """
        self.database = database
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Inspection History")
        self.window.geometry("900x700")
        
        self._build_ui()
        self._load_data()
        
        print("[UI] History window opened")
    
    def _build_ui(self):
        """Build the user interface"""
        # Configure style
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Arial", 14, "bold"))
        
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # === TOP - Statistics ===
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics Summary", padding="10")
        stats_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        stats_frame.columnconfigure(0, weight=1)
        
        self.stats_label = ttk.Label(stats_frame, text="Loading...", font=("Arial", 10), justify=tk.LEFT)
        self.stats_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # === MIDDLE - History Table ===
        table_frame = ttk.LabelFrame(main_frame, text="Inspection History", padding="10")
        table_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Create Treeview with scrollbar
        tree_scroll = ttk.Scrollbar(table_frame)
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=("ID", "Time", "Result", "Reason", "Cap", "Filled", "Label"),
            show="headings",
            yscrollcommand=tree_scroll.set
        )
        
        tree_scroll.config(command=self.tree.yview)
        
        # Define columns
        self.tree.heading("ID", text="ID")
        self.tree.heading("Time", text="Timestamp")
        self.tree.heading("Result", text="Result")
        self.tree.heading("Reason", text="Reason")
        self.tree.heading("Cap", text="Cap")
        self.tree.heading("Filled", text="Filled")
        self.tree.heading("Label", text="Label")
        
        # Column widths
        self.tree.column("ID", width=50, anchor=tk.CENTER)
        self.tree.column("Time", width=150, anchor=tk.CENTER)
        self.tree.column("Result", width=80, anchor=tk.CENTER)
        self.tree.column("Reason", width=300, anchor=tk.W)
        self.tree.column("Cap", width=60, anchor=tk.CENTER)
        self.tree.column("Filled", width=60, anchor=tk.CENTER)
        self.tree.column("Label", width=60, anchor=tk.CENTER)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bind double-click to show image
        self.tree.bind("<Double-1>", self.on_row_double_click)
        
        # === BOTTOM - Controls ===
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        refresh_btn = ttk.Button(control_frame, text="🔄 Refresh", command=self._load_data)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        clear_btn = ttk.Button(control_frame, text="🗑️ Clear History", command=self.clear_history)
        clear_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        defects_btn = ttk.Button(control_frame, text="📊 Defect Summary", command=self.show_defect_summary)
        defects_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        close_btn = ttk.Button(control_frame, text="Close", command=self.window.destroy)
        close_btn.pack(side=tk.RIGHT)
    
    def _load_data(self):
        """Load data from database"""
        # Get statistics
        stats = self.database.get_statistics()
        
        # Format statistics text
        stats_text = "TODAY:\n"
        stats_text += f"  Total: {stats['today']['total']}\n"
        stats_text += f"  OK: {stats['today']['ok']} ({stats['today']['ok_rate']:.1f}%)\n"
        stats_text += f"  NG: {stats['today']['ng']} ({stats['today']['ng_rate']:.1f}%)\n\n"
        
        stats_text += "ALL TIME:\n"
        stats_text += f"  Total: {stats['all_time']['total']}\n"
        stats_text += f"  OK: {stats['all_time']['ok']} ({stats['all_time']['ok_rate']:.1f}%)\n"
        stats_text += f"  NG: {stats['all_time']['ng']} ({stats['all_time']['ng_rate']:.1f}%)"
        
        self.stats_label.config(text=stats_text)
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Load recent inspections
        records = self.database.get_recent_inspections(limit=100)
        
        for record in records:
            # Format boolean values
            cap = "✓" if record['has_cap'] else "✗"
            filled = "✓" if record['has_filled'] else "✗"
            label = "✓" if record['has_label'] else "✗"
            
            # Add to tree
            item_id = self.tree.insert(
                "",
                tk.END,
                values=(
                    record['id'],
                    record['timestamp'],
                    record['result'],
                    record['reason'],
                    cap,
                    filled,
                    label
                ),
                tags=(record['result'],)
            )
        
        # Color code rows
        self.tree.tag_configure('OK', background='#d4edda')
        self.tree.tag_configure('NG', background='#f8d7da')
        
        print(f"[UI] Loaded {len(records)} inspection records")
    
    def on_row_double_click(self, event):
        """Handle double-click on row to show image"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        record_id = item['values'][0]
        
        # Get full record
        records = self.database.get_recent_inspections(limit=1000)
        record = next((r for r in records if r['id'] == record_id), None)
        
        if not record:
            return
        
        # Show image if available
        image_path = record.get('image_path', '')
        if image_path and os.path.exists(image_path):
            self._show_image(image_path, record)
        else:
            messagebox.showinfo("No Image", "Image file not found or not saved.")
    
    def _show_image(self, image_path, record):
        """Show image in popup window"""
        try:
            # Create popup window
            popup = tk.Toplevel(self.window)
            popup.title(f"Inspection #{record['id']} - {record['result']}")
            popup.geometry("700x600")
            
            # Info frame
            info_frame = ttk.Frame(popup, padding="10")
            info_frame.pack(fill=tk.X)
            
            info_text = f"Time: {record['timestamp']}\n"
            info_text += f"Result: {record['result']}\n"
            info_text += f"Reason: {record['reason']}\n"
            info_text += f"Processing Time: {record['processing_time']:.3f}s"
            
            info_label = ttk.Label(info_frame, text=info_text, font=("Arial", 10))
            info_label.pack()
            
            # Image frame
            img_frame = ttk.Frame(popup, padding="10")
            img_frame.pack(fill=tk.BOTH, expand=True)
            
            # Load and display image
            img = cv2.imread(image_path)
            if img is not None:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = cv2.resize(img, (640, 480))
                
                photo = ImageTk.PhotoImage(image=Image.fromarray(img))
                
                img_label = ttk.Label(img_frame, image=photo)
                img_label.image = photo  # Keep reference
                img_label.pack()
            else:
                ttk.Label(img_frame, text="Failed to load image").pack()
            
            # Close button
            ttk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display image:\n{e}")
    
    def clear_history(self):
        """Clear inspection history"""
        if not messagebox.askyesno("Confirm", "Are you sure you want to clear all inspection history?"):
            return
        
        if self.database.clear_history():
            messagebox.showinfo("Success", "History cleared successfully")
            self._load_data()
        else:
            messagebox.showerror("Error", "Failed to clear history")
    
    def show_defect_summary(self):
        """Show defect type summary"""
        defects = self.database.get_defect_summary()
        
        # Create popup window
        popup = tk.Toplevel(self.window)
        popup.title("Defect Summary")
        popup.geometry("400x400")
        
        # Title
        title_frame = ttk.Frame(popup, padding="10")
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text="Defect Type Summary", 
                 font=("Arial", 12, "bold")).pack()
        
        # Defect list
        list_frame = ttk.Frame(popup, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        for defect_type, count in defects.items():
            row = ttk.Frame(list_frame)
            row.pack(fill=tk.X, pady=5)
            
            ttk.Label(row, text=defect_type, font=("Arial", 10)).pack(side=tk.LEFT)
            ttk.Label(row, text=f"{count} occurrences", 
                     font=("Arial", 10, "bold")).pack(side=tk.RIGHT)
        
        # Close button
        ttk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)

