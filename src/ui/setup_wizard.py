"""
首次启动向导
=============
使用 tkinter Toplevel + 多步 Frame 切换实现向导流程。

流程: 欢迎 -> 填写配置 -> 测试连接 -> 完成
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import logging

from ui.styles import (
    COLOR_PRIMARY, COLOR_BG, COLOR_BG_WHITE, COLOR_TEXT, COLOR_TEXT_SECONDARY,
    COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING,
    FONT_NORMAL, FONT_BOLD, FONT_TITLE, FONT_SECTION
)

logger = logging.getLogger(__name__)


class SetupWizard(tk.Toplevel):
    """
    首次启动配置向导。

    使用方式:
        wizard = SetupWizard(parent)
        parent.wait_window(wizard)
        config = wizard.get_connection_config()
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.title("ServerControl - 初始配置向导")
        self.geometry("560x480")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)
        self.transient(parent)
        self.grab_set()

        self._result = None
        self._current_page = 0
        self._pages = []
        self._ssh_manager = None
        self._test_passed = False

        # 配置数据
        self._config = {
            "name": "我的服务器",
            "host": "",
            "port": 22,
            "username": "root",
            "password": "",
            "key_file": None,
        }

        self._init_ui()

        # 居中
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _init_ui(self):
        # 标题区域
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=24, pady=(16, 8))
        self._title_label = ttk.Label(title_frame, text="", style="Title.TLabel")
        self._title_label.pack(side=tk.LEFT)
        self._page_label = ttk.Label(title_frame, text="", style="Secondary.TLabel")
        self._page_label.pack(side=tk.RIGHT)

        ttk.Separator(self).pack(fill=tk.X, padx=24, pady=4)

        # 内容区域
        self._content_frame = ttk.Frame(self, style="Card.TFrame")
        self._content_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)

        # 构建各页面
        self._page_welcome = self._build_welcome()
        self._page_config = self._build_config()
        self._page_test = self._build_test()
        self._page_finish = self._build_finish()
        self._pages = [self._page_welcome, self._page_config,
                       self._page_test, self._page_finish]

        # 底部按钮区域
        ttk.Separator(self).pack(fill=tk.X, padx=24, pady=4)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=24, pady=(8, 16))

        self._back_btn = ttk.Button(btn_frame, text="上一步", style="TButton",
                                      command=self._go_back)
        self._back_btn.pack(side=tk.LEFT)

        self._cancel_btn = ttk.Button(btn_frame, text="取消", style="TButton",
                                        command=self.destroy)
        self._cancel_btn.pack(side=tk.RIGHT)

        self._next_btn = ttk.Button(btn_frame, text="下一步", style="Primary.TButton",
                                      command=self._go_next)
        self._next_btn.pack(side=tk.RIGHT, padx=(0, 8))

        self._show_page(0)

    # ── 页面构建 ──────────────────────────────────────────────────────────────

    def _build_welcome(self) -> ttk.Frame:
        """欢迎页面。"""
        frame = ttk.Frame(self._content_frame, style="Card.TFrame")

        ttk.Label(frame, text="欢迎使用 ServerControl",
                  style="Title.TLabel").pack(anchor=tk.W, pady=(20, 8))
        ttk.Label(frame, text="这是一款简单易用的远程服务器管理工具，接下来将引导您完成初始配置。",
                  style="TLabel", wraplength=460).pack(anchor=tk.W, pady=4)

        steps = ttk.Frame(frame, style="Card.TFrame")
        steps.pack(fill=tk.X, pady=(20, 0))
        for i, step in enumerate(["配置服务器连接信息", "测试连接是否正常", "安全保存您的凭据"], 1):
            ttk.Label(steps, text=f"  {i}. {step}", style="TLabel").pack(anchor=tk.W, pady=4)

        ttk.Label(frame, text="请准备好您的服务器地址、用户名和密码（或私钥文件），然后点击 [下一步] 继续。",
                  style="Secondary.TLabel", wraplength=460).pack(anchor=tk.W, pady=(20, 0))
        return frame

    def _build_config(self) -> ttk.Frame:
        """配置填写页面。"""
        frame = ttk.Frame(self._content_frame, style="Card.TFrame")

        ttk.Label(frame, text="填写服务器信息", style="Title.TLabel").pack(anchor=tk.W, pady=(10, 4))
        ttk.Label(frame, text="请输入您要连接的服务器基本信息。",
                  style="Secondary.TLabel").pack(anchor=tk.W, pady=2)

        # 基本信息表单
        form = ttk.Frame(frame, style="Card.TFrame")
        form.pack(fill=tk.X, pady=(10, 4))

        self._name_var = tk.StringVar(value="我的服务器")
        self._host_var = tk.StringVar()
        self._port_var = tk.IntVar(value=22)
        self._username_var = tk.StringVar(value="root")

        fields = [
            ("连接名称:", self._name_var),
            ("服务器地址:", self._host_var),
            ("SSH 端口:", self._port_var),
            ("用户名:", self._username_var),
        ]
        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky=tk.W, pady=4, padx=(0, 8))
            if label == "SSH 端口:":
                ttk.Spinbox(form, textvariable=var, from_=1, to=65535, width=8).grid(
                    row=i, column=1, sticky=tk.W, pady=4)
            else:
                ttk.Entry(form, textvariable=var, width=30).grid(
                    row=i, column=1, sticky=tk.EW, pady=4)
        form.columnconfigure(1, weight=1)

        # 认证方式
        auth_frame = ttk.LabelFrame(frame, text="认证方式", padding=10)
        auth_frame.pack(fill=tk.X, pady=(8, 4))

        self._auth_mode = tk.StringVar(value="password")

        ttk.Radiobutton(auth_frame, text="使用密码登录（推荐）",
                         variable=self._auth_mode, value="password",
                         command=self._toggle_auth).grid(row=0, column=0, sticky=tk.W, pady=2)

        self._password_var = tk.StringVar()
        ttk.Entry(auth_frame, textvariable=self._password_var, show="*").grid(
            row=1, column=0, sticky=tk.EW, padx=(28, 0), pady=2)

        ttk.Radiobutton(auth_frame, text="使用私钥文件登录",
                         variable=self._auth_mode, value="keyfile",
                         command=self._toggle_auth).grid(row=2, column=0, sticky=tk.W, pady=2)

        key_inner = ttk.Frame(auth_frame)
        key_inner.grid(row=3, column=0, sticky=tk.EW, padx=(28, 0), pady=2)
        self._keyfile_var = tk.StringVar()
        self._keyfile_entry = ttk.Entry(key_inner, textvariable=self._keyfile_var,
                                          state=tk.DISABLED, width=28)
        self._keyfile_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._browse_btn = ttk.Button(key_inner, text="浏览", style="TButton",
                                        command=self._browse_key, state=tk.DISABLED)
        self._browse_btn.pack(side=tk.RIGHT, padx=(4, 0))

        auth_frame.columnconfigure(0, weight=1)
        return frame

    def _build_test(self) -> ttk.Frame:
        """测试连接页面。"""
        frame = ttk.Frame(self._content_frame, style="Card.TFrame")

        ttk.Label(frame, text="测试连接", style="Title.TLabel").pack(anchor=tk.W, pady=(10, 4))
        ttk.Label(frame, text="点击下方按钮测试服务器连接是否正常。",
                  style="Secondary.TLabel").pack(anchor=tk.W, pady=2)

        self._test_btn = ttk.Button(frame, text="开始测试", style="Primary.TButton",
                                      command=self._start_test)
        self._test_btn.pack(pady=(30, 10))

        self._test_status = ttk.Label(frame, text="等待测试...", style="Connecting.TLabel")
        self._test_status.pack(pady=4)

        self._test_detail = ttk.Label(frame, text="", style="Secondary.TLabel",
                                       wraplength=400, justify=tk.CENTER)
        self._test_detail.pack(pady=4)

        return frame

    def _build_finish(self) -> ttk.Frame:
        """完成页面。"""
        frame = ttk.Frame(self._content_frame, style="Card.TFrame")

        ttk.Label(frame, text="配置完成", style="Title.TLabel").pack(anchor=tk.W, pady=(10, 4))

        self._finish_msg = ttk.Label(frame,
            text="恭喜！服务器连接配置已保存，您可以开始使用 ServerControl 了。",
            style="TLabel", wraplength=460)
        self._finish_msg.pack(anchor=tk.W, pady=(30, 4))

        return frame

    # ── 导航逻辑 ──────────────────────────────────────────────────────────────

    def _show_page(self, index: int):
        """显示指定页面。"""
        self._current_page = index
        # 隐藏所有页面
        for page in self._pages:
            page.pack_forget()
        self._pages[index].pack(fill=tk.BOTH, expand=True)

        # 更新标题和页码
        titles = ["欢迎使用", "填写服务器信息", "测试连接", "配置完成"]
        self._title_label.config(text=titles[index])
        self._page_label.config(text=f"步骤 {index + 1} / {len(self._pages)}")

        # 按钮状态
        self._back_btn.config(state=tk.NORMAL if index > 0 else tk.DISABLED)

        if index == 0:
            self._next_btn.config(text="下一步")
        elif index == len(self._pages) - 2:  # 测试页
            self._next_btn.config(text="下一步", state=tk.DISABLED if not self._test_passed else tk.NORMAL)
        elif index == len(self._pages) - 1:  # 完成页
            self._next_btn.config(text="完成")
            self._cancel_btn.config(text="关闭")
        else:
            self._next_btn.config(text="下一步", state=tk.NORMAL)

    def _go_next(self):
        """下一步。"""
        if self._current_page == 1:
            # 验证配置
            if not self._validate_config():
                return
            self._save_config_from_form()
        elif self._current_page == 2:
            # 测试页 -> 完成页，保存凭据
            self._save_credentials()
        elif self._current_page == len(self._pages) - 1:
            # 完成页 -> 关闭向导
            self._save_config_from_form()
            self._result = dict(self._config)
            self.destroy()
            return

        if self._current_page < len(self._pages) - 1:
            self._show_page(self._current_page + 1)

    def _go_back(self):
        """上一步。"""
        if self._current_page > 0:
            self._show_page(self._current_page - 1)

    # ── 配置验证与保存 ──────────────────────────────────────────────────────────

    def _validate_config(self) -> bool:
        """验证配置表单。"""
        name = self._name_var.get().strip()
        host = self._host_var.get().strip()
        username = self._username_var.get().strip()

        if not name:
            messagebox.showwarning("提示", "请填写连接名称。")
            return False
        if not host:
            messagebox.showwarning("提示", "请填写服务器地址。")
            return False
        if not username:
            messagebox.showwarning("提示", "请填写用户名。")
            return False
        if self._auth_mode.get() == "password" and not self._password_var.get():
            messagebox.showwarning("提示", "请填写密码。")
            return False
        if self._auth_mode.get() == "keyfile" and not self._keyfile_var.get().strip():
            messagebox.showwarning("提示", "请选择私钥文件路径。")
            return False
        return True

    def _save_config_from_form(self):
        """从表单更新配置字典。"""
        self._config["name"] = self._name_var.get().strip()
        self._config["host"] = self._host_var.get().strip()
        self._config["port"] = self._port_var.get()
        self._config["username"] = self._username_var.get().strip()
        if self._auth_mode.get() == "password":
            self._config["password"] = self._password_var.get()
            self._config["key_file"] = None
        else:
            self._config["password"] = None
            self._config["key_file"] = self._keyfile_var.get().strip()

    def _toggle_auth(self):
        """切换认证方式。"""
        is_key = self._auth_mode.get() == "keyfile"
        key_state = tk.NORMAL if is_key else tk.DISABLED
        self._keyfile_entry.config(state=key_state)
        self._browse_btn.config(state=key_state)

    def _browse_key(self):
        """选择密钥文件。"""
        path = filedialog.askopenfilename(title="选择私钥文件",
                                            filetypes=[("所有文件", "*.*")])
        if path:
            self._keyfile_var.set(path)

    # ── 测试连接 ──────────────────────────────────────────────────────────────

    def _start_test(self):
        """开始测试连接。"""
        self._save_config_from_form()
        self._test_btn.config(state=tk.DISABLED)
        self._test_status.config(text="正在连接...", style="Connecting.TLabel")
        self._test_detail.config(text="")

        def _do_test():
            from core.ssh_manager import SSHManager
            mgr = SSHManager()
            try:
                mgr.connect(
                    host=self._config["host"],
                    port=self._config["port"],
                    username=self._config["username"],
                    password=self._config.get("password"),
                    key_file=self._config.get("key_file"),
                )
                mgr.disconnect()
                self.after(0, lambda: self._on_test_done(True, "连接成功！"))
            except Exception as e:
                from utils.error_messages import format_error
                self.after(0, lambda: self._on_test_done(False, format_error(e)))

        threading.Thread(target=_do_test, daemon=True).start()

    def _on_test_done(self, success: bool, message: str):
        """测试完成回调。"""
        self._test_btn.config(state=tk.NORMAL)
        if success:
            self._test_passed = True
            self._test_status.config(text="连接成功", style="Connected.TLabel")
            self._test_detail.config(text=message)
            self._next_btn.config(state=tk.NORMAL)
        else:
            self._test_passed = False
            self._test_status.config(text="连接失败", style="Disconnected.TLabel")
            self._test_detail.config(text=message)

    def _save_credentials(self):
        """保存凭据。"""
        from security.credential_store import CredentialStore
        store = CredentialStore()
        name = self._config["name"]
        if self._config.get("password"):
            store.set_password(name, self._config["password"])
        if self._config.get("key_file"):
            store.set_key_path(name, self._config["key_file"])
        logger.info("首次配置已保存: %s", name)

    def get_connection_config(self) -> dict | None:
        """获取向导结果（关闭后调用）。"""
        return self._result
