"""
应用启动器
==========
创建主窗口，处理全局异常。
"""
import sys
import traceback
import logging
import tkinter as tk
from tkinter import messagebox

logger = logging.getLogger(__name__)


class ServerControlApp:
    """
    应用控制器。

    职责:
        - 创建并配置主窗口
        - 应用 ttk 主题
        - 全局异常捕获
    """

    def __init__(self):
        self._root = None

    def run(self):
        """启动应用。"""
        try:
            self._install_exception_hook()

            self._root = tk.Tk()
            self._root.withdraw()

            from ui.styles import apply_theme
            # 获取屏幕尺寸并传递给主题应用函数
            self._root.update_idletasks()
            screen_width = self._root.winfo_screenwidth()
            screen_height = self._root.winfo_screenheight()
            apply_theme(self._root, screen_width, screen_height)

            # 直接启动主窗口
            self._show_main_window()

            # _root 可能在上述方法中被设置为 None，需要检查
            if self._root is not None:
                self._root.mainloop()

        except Exception as e:
            logger.critical("应用启动失败: %s", e, exc_info=True)
            try:
                messagebox.showerror("启动失败", f"ServerControl 启动失败:\n{e}")
            except Exception:
                pass
            sys.exit(1)

    def _show_main_window(self):
        """直接显示主窗口。"""
        self._root.destroy()
        self._root = None
        self._launch_main()

    def _launch_main(self):
        """启动主窗口。"""
        from ui.main_window import MainWindow
        window = MainWindow()
        window.mainloop()

    def _install_exception_hook(self):
        """安装全局异常钩子。"""
        def _hook(exc_type, exc_value, exc_tb):
            logger.critical("未捕获异常: %s", exc_value,
                          exc_info=(exc_type, exc_value, exc_tb))
            try:
                msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
                messagebox.showerror("程序错误", f"发生未预期的错误:\n\n{msg}")
            except Exception:
                pass
        sys.excepthook = _hook
