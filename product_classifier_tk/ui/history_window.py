"""History window for viewing stored inspection records."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from typing import Optional

from core.database import ProductDatabase


class HistoryWindow(tk.Toplevel):
    """Displays historical detection records with filtering and CSV export."""

    def __init__(self, master: tk.Misc, database: ProductDatabase) -> None:
        super().__init__(master)
        self.title("History - Product Classification")
        self.geometry("700x400")
        self.database = database

        self.filter_var = tk.StringVar(value="ALL")

        self._build_widgets()
        self._load_records()

    def _build_widgets(self) -> None:
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(control_frame, text="Filter:").pack(side=tk.LEFT)
        filter_combo = ttk.Combobox(
            control_frame,
            textvariable=self.filter_var,
            values=["ALL", "GOOD", "BAD"],
            state="readonly",
            width=10,
        )
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", lambda _evt: self._load_records())

        export_btn = ttk.Button(control_frame, text="Export CSV", command=self._export_csv)
        export_btn.pack(side=tk.RIGHT)

        self.tree = ttk.Treeview(
            self,
            columns=("id", "timestamp", "result", "confidence"),
            show="headings",
        )
        for col, text, width in (
            ("id", "ID", 50),
            ("timestamp", "Timestamp", 200),
            ("result", "Result", 100),
            ("confidence", "Confidence", 100),
        ):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _load_records(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        filter_value: Optional[str] = None
        if self.filter_var.get() in {"GOOD", "BAD"}:
            filter_value = self.filter_var.get()

        rows = self.database.fetch_results(filter_value)
        for row in rows:
            self.tree.insert("", tk.END, values=row)

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export history",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return

        try:
            filter_value: Optional[str] = None
            if self.filter_var.get() in {"GOOD", "BAD"}:
                filter_value = self.filter_var.get()
            self.database.export_to_csv(Path(path), filter_value)
            messagebox.showinfo("Export complete", f"History exported to {path}")
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))

