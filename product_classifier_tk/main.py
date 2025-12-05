"""Entry point - Phân loại sản phẩm Coca-Cola."""
from pathlib import Path
from ui.main_window import MainWindow


def main():
    """Khởi chạy ứng dụng."""
    project_root = Path(__file__).resolve().parent
    
    app = MainWindow(
        model_path=project_root / "model" / "my_model.pt",
        database_path=project_root / "database" / "products.db"
    )
    app.mainloop()


if __name__ == "__main__":
    main()
