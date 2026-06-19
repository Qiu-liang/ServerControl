"""
ServerControl 入口点
===================
启动 tkinter 应用，隐藏控制台窗口（Windows）。
"""
import sys
import os

# 确保 src 目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 初始化日志
from utils.logger import setup_logger
setup_logger()


def main():
    # Windows 隐藏控制台窗口
    if sys.platform == "win32":
        try:
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass

    from app import ServerControlApp
    app = ServerControlApp()
    app.run()


if __name__ == "__main__":
    main()
