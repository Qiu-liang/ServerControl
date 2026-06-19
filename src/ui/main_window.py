"""
主窗口
======
使用 tkinter 组装所有 UI 组件，管理信号/槽、连接状态。
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import logging

from ui.styles import (
    COLOR_PRIMARY, COLOR_BG, COLOR_BG_WHITE, COLOR_TEXT, COLOR_TEXT_SECONDARY,
    COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING,
    FONT_NORMAL, FONT_BOLD, FONT_TITLE, FONT_SECTION, FONT_SMALL,
    get_scaled_font, get_scaled_size, get_scale_factor
)
from ui.output_console import OutputConsole
from ui.command_panel import CommandPanel
from ui.session_manager import SessionManager
from ui.connection_dialog import ConnectionDialog
from core.ssh_manager import SSHManager
from core.sftp_browser import SFTPBrowser
from core.command_registry import CommandRegistry
from workers import TaskRunner, StreamTaskRunner

logger = logging.getLogger(__name__)


class MainWindow(tk.Tk):
    """应用主窗口。"""

    def __init__(self):
        super().__init__()
        self.title("ServerControl - 远程服务器管理工具")
        self.configure(bg=COLOR_BG)

        # 获取屏幕尺寸并动态计算窗口大小
        self.update_idletasks()
        self._screen_width = self.winfo_screenwidth()
        self._screen_height = self.winfo_screenheight()

        # 动态计算窗口大小（屏幕的 48% 宽度，51% 高度）
        self._window_width = int(self._screen_width * 0.48)
        self._window_height = int(self._screen_height * 0.51)

        # 最小尺寸限制
        self._window_width = max(900, self._window_width)
        self._window_height = max(600, self._window_height)

        self.minsize(900, 600)

        # 窗口居中显示
        x = (self._screen_width - self._window_width) // 2
        y = (self._screen_height - self._window_height) // 2
        self.geometry(f"{self._window_width}x{self._window_height}+{x}+{y}")

        # 核心组件
        self._ssh_manager = SSHManager()
        self._sftp_browser = None  # 连接成功后创建
        self._cmd_registry = CommandRegistry()
        self._cmd_registry.load()
        self._task_runner = TaskRunner(self)
        self._stream_runner = StreamTaskRunner(self)
        self._connected = False
        self._current_config = None

        self._init_ui()
        self._init_menu()
        self._load_commands()

        # 关闭窗口事件
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_ui(self):
        # 顶部工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=8, pady=(8, 4))

        self._connect_btn = ttk.Button(toolbar, text="连接", style="Success.TButton",
                                         command=self._on_connect)
        self._connect_btn.pack(side=tk.LEFT, padx=2)

        self._disconnect_btn = ttk.Button(toolbar, text="断开", style="Danger.TButton",
                                            command=self._on_disconnect, state=tk.DISABLED)
        self._disconnect_btn.pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)

        self._status_label = ttk.Label(toolbar, text="[未连接]",
                                         style="Disconnected.TLabel")
        self._status_label.pack(side=tk.LEFT, padx=4)

        self._conn_name_label = ttk.Label(toolbar, text="", style="Secondary.TLabel")
        self._conn_name_label.pack(side=tk.LEFT, padx=4)

        # 自定义命令输入
        ttk.Label(toolbar, text="自定义命令:").pack(side=tk.LEFT, padx=(16, 4))
        self._custom_cmd_var = tk.StringVar()
        self._custom_cmd_entry = ttk.Entry(toolbar, textvariable=self._custom_cmd_var, width=24)
        self._custom_cmd_entry.pack(side=tk.LEFT, padx=2)
        self._custom_cmd_entry.bind("<Return>", lambda e: self._run_custom_command())

        self._run_btn = ttk.Button(toolbar, text="执行", style="Primary.TButton",
                                     command=self._run_custom_command, state=tk.DISABLED)
        self._run_btn.pack(side=tk.LEFT, padx=4)

        # 主体三栏布局
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # 左侧：会话管理器
        left_frame = ttk.Frame(main_pane, style="Card.TFrame", width=250)
        self._session_manager = SessionManager(
            left_frame,
            on_session_connect=self._on_session_connect,
            on_session_edit=self._on_session_edit
        )
        self._session_manager.pack(fill=tk.BOTH, expand=True)
        main_pane.add(left_frame, weight=1)

        # 中间：命令面板
        mid_frame = ttk.Frame(main_pane, style="Card.TFrame", width=300)
        self._cmd_panel = CommandPanel(
            mid_frame,
            on_command_selected=self._on_command_selected
        )
        self._cmd_panel.pack(fill=tk.BOTH, expand=True)
        main_pane.add(mid_frame, weight=1)

        # 右侧：输出控制台
        right_frame = ttk.Frame(main_pane, style="Card.TFrame", width=450)
        self._console = OutputConsole(right_frame)
        self._console.pack(fill=tk.BOTH, expand=True)
        main_pane.add(right_frame, weight=2)

        # 状态栏
        status_bar = ttk.Frame(self)
        status_bar.pack(fill=tk.X, padx=8, pady=(0, 4))
        self._statusbar_label = ttk.Label(status_bar, text="就绪", style="Secondary.TLabel")
        self._statusbar_label.pack(side=tk.LEFT, padx=4)

    def _init_menu(self):
        """初始化菜单栏。"""
        menubar = tk.Menu(self)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建连接", command=self._on_new_connection)
        file_menu.add_command(label="编辑当前连接", command=self._on_edit_connection)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_close)
        menubar.add_cascade(label="文件", menu=file_menu)

        # 命令菜单
        cmd_menu = tk.Menu(menubar, tearoff=0)
        cmd_menu.add_command(label="执行自定义命令", command=self._run_custom_command)
        cmd_menu.add_command(label="停止当前命令", command=self._stop_command)
        menubar.add_cascade(label="命令", menu=cmd_menu)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="项目地址", command=self._open_github)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.config(menu=menubar)

    def _load_commands(self):
        """加载命令注册表到面板。"""
        categories = self._cmd_registry.get_categories()
        self._cmd_panel.load_commands(categories)

    # ── 连接管理 ──────────────────────────────────────────────────────────────

    def _on_connect(self):
        """连接按钮 -> 打开连接对话框。"""
        dialog = ConnectionDialog(self, title="连接服务器")
        self.wait_window(dialog)
        result = dialog.get_result()
        if result:
            self._do_connect(result)

    def _on_new_connection(self):
        """菜单 -> 新建连接。"""
        self._on_connect()

    def _on_edit_connection(self):
        """菜单 -> 编辑当前连接。"""
        if self._current_config:
            dialog = ConnectionDialog(self, initial_config=self._current_config,
                                        title="编辑连接")
            self.wait_window(dialog)
            result = dialog.get_result()
            if result:
                if self._connected:
                    self._on_disconnect()
                self._do_connect(result)

    def _do_connect(self, config: dict):
        """执行连接。"""
        self._set_status("connecting")
        self._current_config = config
        self._console.append_info(f"正在连接 {config['host']}:{config['port']}...")

        def _connect_task():
            self._ssh_manager.connect(
                host=config["host"],
                port=config["port"],
                username=config["username"],
                password=config.get("password"),
                key_file=config.get("key_file"),
            )
            return True

        self._task_runner.run(
            task=_connect_task,
            on_success=lambda _: self._on_connected(config),
            on_error=lambda msg: self._on_connect_failed(msg, config)
        )

    def _on_connected(self, config: dict):
        """连接成功回调。"""
        self._connected = True
        # 创建 SFTP 浏览器
        self._sftp_browser = SFTPBrowser(self._ssh_manager.client)
        self._set_status("connected", config["name"])
        self._console.append_success(f"成功连接到 {config['name']} ({config['host']})")
        self._connect_btn.config(state=tk.DISABLED)
        self._disconnect_btn.config(state=tk.NORMAL)
        self._run_btn.config(state=tk.NORMAL)
        self._cmd_panel.set_connected(True)
        
        # 保存连接配置（不含密码）
        from security.credential_store import CredentialStore
        store = CredentialStore()
        store.set_connection(config["name"], {
            "name": config["name"],
            "host": config["host"],
            "port": config["port"],
            "username": config["username"]
        })
        
        # 如果用户选择了保存密码，则保存密码
        if config.get("save_password") and config.get("password"):
            store.set_password(config["username"], config["password"])
        
        # 保存会话历史记录
        self._session_manager.add_session(config["name"], config, success=True)

    def _on_connect_failed(self, msg: str, config: dict):
        """连接失败回调。"""
        self._set_status("disconnected")
        self._console.append_output(f"连接失败: {msg}", is_error=True)
        self._connect_btn.config(state=tk.NORMAL)
        
        # 保存失败的会话历史记录
        self._session_manager.add_session(config["name"], config, success=False)

    def _on_disconnect(self):
        """断开连接。"""
        if self._sftp_browser:
            self._sftp_browser.close()
            self._sftp_browser = None
        self._ssh_manager.disconnect()
        self._connected = False
        self._set_status("disconnected")
        self._console.append_info("已断开连接。")
        self._connect_btn.config(state=tk.NORMAL)
        self._disconnect_btn.config(state=tk.DISABLED)
        self._run_btn.config(state=tk.DISABLED)
        self._cmd_panel.set_connected(False)

    def _set_status(self, state: str, name: str = ""):
        """更新状态栏。"""
        if state == "connected":
            self._status_label.config(text="[已连接]", style="Connected.TLabel")
            self._conn_name_label.config(text=name)
            self._statusbar_label.config(text=f"已连接: {name}")
        elif state == "connecting":
            self._status_label.config(text="[连接中...]", style="Connecting.TLabel")
            self._conn_name_label.config(text="")
            self._statusbar_label.config(text="正在连接...")
        else:
            self._status_label.config(text="[未连接]", style="Disconnected.TLabel")
            self._conn_name_label.config(text="")
            self._statusbar_label.config(text="就绪")

    # ── 命令执行 ──────────────────────────────────────────────────────────────

    def _on_command_selected(self, cmd: dict):
        """命令面板按钮点击。"""
        if not self._connected:
            return
        command = cmd.get("command", "")
        name = cmd.get("name", "未知命令")

        if not messagebox.askyesno("确认执行", f"确定要执行 [{name}] 吗?\n\n命令: {command}"):
            return

        self._execute_command(command, name)

    def _run_custom_command(self):
        """执行自定义命令。"""
        if not self._connected:
            messagebox.showwarning("提示", "请先连接服务器。")
            return
        cmd = self._custom_cmd_var.get().strip()
        if not cmd:
            return
        self._execute_command(cmd, f"自定义: {cmd}")

    def _execute_command(self, command: str, name: str = ""):
        """执行命令（流式输出）。"""
        self._console.append_command_header(f"{name}\n{command}")

        def _on_output(text, is_err):
            self._console.append_output(text, is_err)

        def _on_finished(exit_code):
            self._console.append_command_footer(exit_code)

        def _on_error(msg):
            self._console.append_output(f"执行失败: {msg}", is_error=True)

        self._stream_runner.run_command(
            ssh_manager=self._ssh_manager,
            command=command,
            on_output=_on_output,
            on_finished=_on_finished,
            on_error=_on_error
        )

    def _stop_command(self):
        """停止当前命令。"""
        self._stream_runner.cancel()
        self._console.append_info("已发送停止信号。")

    # ── 会话管理 ──────────────────────────────────────────────────────────────

    def _on_session_connect(self, session: dict):
        """会话管理器连接回调。"""
        # 从会话历史中获取连接配置
        config = {
            "name": session.get("name", ""),
            "host": session.get("host", ""),
            "port": session.get("port", 22),
            "username": session.get("username", "")
        }
        
        # 检查是否有完整的连接配置
        from security.credential_store import CredentialStore
        store = CredentialStore()
        full_config = store.get_connection(config["name"])
        if full_config:
            config = full_config
            # 尝试获取保存的密码
            password = store.get_password(config.get("username", ""))
            if password:
                config["password"] = password
        
        # 如果没有密码或密钥文件，弹出连接对话框让用户输入
        if not config.get("password") and not config.get("key_file"):
            dialog = ConnectionDialog(self, initial_config=config, title="连接服务器")
            self.wait_window(dialog)
            result = dialog.get_result()
            if result:
                self._do_connect(result)
            return
        
        # 执行连接
        self._do_connect(config)

    def _on_session_edit(self, session: dict):
        """会话管理器编辑回调。"""
        # 从会话历史中获取连接配置
        config = {
            "name": session.get("name", ""),
            "host": session.get("host", ""),
            "port": session.get("port", 22),
            "username": session.get("username", "")
        }
        
        # 检查是否有完整的连接配置
        from security.credential_store import CredentialStore
        store = CredentialStore()
        full_config = store.get_connection(config["name"])
        if full_config:
            config = full_config
        
        # 打开编辑对话框
        dialog = ConnectionDialog(self, initial_config=config, title="编辑连接")
        self.wait_window(dialog)
        result = dialog.get_result()
        if result:
            if self._connected:
                self._on_disconnect()
            self._do_connect(result)

    # ── 其他菜单 ──────────────────────────────────────────────────────────────

    def _open_commands_json(self):
        """打开 commands.json 文件。"""
        import subprocess
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                            "config", "commands.json")
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showinfo("提示", f"命令配置文件不存在: {path}")

    def _open_github(self):
        """打开项目 GitHub 地址。"""
        import webbrowser
        webbrowser.open("https://github.com/Qiu-liang/ServerControl")

    def _show_about(self):
        """关于对话框。"""
        messagebox.showinfo("关于",
            "ServerControl v1.0\n\n"
            "远程服务器管理工具\n"
            "使用 tkinter + paramiko 构建\n\n"
            "安全存储: keyring + Fernet 加密")

    def _on_close(self):
        """关闭窗口。"""
        if self._connected:
            self._ssh_manager.disconnect()
        self.destroy()
