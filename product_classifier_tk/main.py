"""Tkinter entry point for the Raspberry Pi product classifier."""
from __future__ import annotations

from pathlib import Path

from ui.main_window import ProductClassifierApp


def main() -> None:
    """Initialize and run the Tkinter application."""
    project_root = Path(__file__).resolve().parent
    model_path = project_root / "model" / "my_model.pt"
    database_path = project_root / "database" / "products.db"

    app = ProductClassifierApp(
        model_path=model_path,
        database_path=database_path,
    )
    app.mainloop()


if __name__ == "__main__":
    main()

