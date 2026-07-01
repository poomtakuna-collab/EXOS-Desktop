__all__ = ["MainWindow"]


def __getattr__(name: str) -> object:
    if name == "MainWindow":
        from src.gui.main_window import MainWindow

        return MainWindow
    raise AttributeError(f"module 'src.gui' has no attribute {name!r}")
