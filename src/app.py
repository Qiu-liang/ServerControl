"""
应用启动器
==========
创建主窗口，处理全局异常，检查首次启动向导。
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
        - 检查是否需要首次配置向导
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
            apply_theme(self._root)

            if self._needs_setup():
                self._run_setup_wizard()
            else:
                self._show_main_window()

            self._root.mainloop()

        except Exception as e:
            logger.critical("应用启动失败: %s", e, exc_info=True)
            try:
                messagebox.showerror("启动失败", f"ServerControl 启动失败:\n{e}")
            except Exception:
                pass
            sys.exit(1)

    def _needs_setup(self) -> bool:
        """检查是否需要首次配置向导。"""
        from security.credential_store import CredentialStore
        store = CredentialStore()
        return not store.list_connections()

    def _run_setup_wizard(self):
        """运行首次配置向导，完成后打开主窗口。"""
        from ui.setup_wizard import SetupWizard
        self._root.deiconify()
        self._root.title("ServerControl - 初始配置向导")

        wizard = SetupWizard(self._root)

        def _on_wizard_close():
            config = wizard.get_connection_config()
            wizard.destroy()
            if config:
                self._root.withdraw()
                self._root.destroy()
                self._root = None
                self._launch_main(config)
            else:
                self._root.destroy()

        wizard.protocol("WM_DELETE_WINDOW", _on_wizard_close)

    def _show_main_window(self):
        """直接显示主窗口。"""
        self._root.destroy()
        self._root = None
        self._launch_main()

    def _launch_main(self, initial_config: dict = None):
        """启动主窗口。"""
        from ui.main_window import MainWindow
        window = MainWindow()
        if initial_config:
            window.after(500, lambda: window._do_connect(initial_config))
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
