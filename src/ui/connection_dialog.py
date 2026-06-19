"""
连接配置对话框
==============
使用 tkinter Toplevel 实现模态对话框，
用于新建/编辑服务器连接配置。
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import threading

from ui.styles import (
    COLOR_PRIMARY, COLOR_BG, COLOR_TEXT, COLOR_TEXT_SECONDARY,
    FONT_NORMAL, FONT_BOLD, FONT_SECTION, FONT_TITLE
)

logger = logging.getLogger(__name__)


class ConnectionDialog(tk.Toplevel):
    """
    新建/编辑连接配置对话框。

    使用方式:
        dialog = ConnectionDialog(parent, initial_config={...})
        parent.wait_window(dialog)
        result = dialog.get_result()  # 返回 dict 或 None（取消）
    """

    def __init__(self, parent, initial_config: dict = None, title: str = "新建连接"):
        super().__init__(parent)
        self.title(title)
        self.geometry("480x520")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)
        self.transient(parent)
        self.grab_set()

        self._result = None
        self._initial = initial_config or {}
        self._init_ui()
        self._load_initial()

        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _init_ui(self):
        pad_x = 20
        pad_y = 8

        # ── 连接名称 ──
        name_frame = ttk.LabelFrame(self, text="连接名称（自定义标识）", padding=10)
        name_frame.pack(fill=tk.X, padx=pad_x, pady=(pad_y, 4))

        self._name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self._name_var)
        name_entry.pack(fill=tk.X)
        name_entry.insert(0, "")

        # ── 服务器信息 ──
        server_frame = ttk.LabelFrame(self, text="服务器信息", padding=10)
        server_frame.pack(fill=tk.X, padx=pad_x, pady=4)

        form = ttk.Frame(server_frame)
        form.pack(fill=tk.X)

        # 地址
        ttk.Label(form, text="服务器地址:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self._host_var = tk.StringVar()
        ttk.Entry(form, textvariable=self._host_var).grid(row=0, column=1,
                                                            sticky=tk.EW, padx=(8, 0), pady=4)
        # 端口
        ttk.Label(form, text="SSH 端口:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self._port_var = tk.IntVar(value=22)
        port_spin = ttk.Spinbox(form, textvariable=self._port_var,
                                  from_=1, to=65535, width=8)
        port_spin.grid(row=1, column=1, sticky=tk.W, padx=(8, 0), pady=4)

        # 用户名
        ttk.Label(form, text="用户名:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self._username_var = tk.StringVar()
        ttk.Entry(form, textvariable=self._username_var).grid(row=2, column=1,
                                                                sticky=tk.EW, padx=(8, 0), pady=4)
        form.columnconfigure(1, weight=1)

        # ── 认证方式 ──
        auth_frame = ttk.LabelFrame(self, text="认证方式", padding=10)
        auth_frame.pack(fill=tk.X, padx=pad_x, pady=4)

        self._auth_mode = tk.StringVar(value="password")

        # 密码选项
        ttk.Radiobutton(auth_frame, text="使用密码登录（推荐）",
                         variable=self._auth_mode, value="password",
                         command=self._toggle_auth).grid(row=0, column=0, sticky=tk.W, pady=2)

        self._password_var = tk.StringVar()
        pwd_entry = ttk.Entry(auth_frame, textvariable=self._password_var, show="*")
        pwd_entry.grid(row=1, column=0, sticky=tk.EW, padx=(24, 0), pady=2)

        # 保存密码选项
        self._save_password_var = tk.BooleanVar(value=False)
        save_pwd_check = ttk.Checkbutton(auth_frame, text="保存密码",
                                          variable=self._save_password_var)
        save_pwd_check.grid(row=2, column=0, sticky=tk.W, padx=(24, 0), pady=2)

        # 密钥选项
        ttk.Radiobutton(auth_frame, text="使用私钥文件登录",
                         variable=self._auth_mode, value="keyfile",
                         command=self._toggle_auth).grid(row=3, column=0, sticky=tk.W, pady=2)

        key_inner = ttk.Frame(auth_frame)
        key_inner.grid(row=4, column=0, sticky=tk.EW, padx=(24, 0), pady=2)

        self._keyfile_var = tk.StringVar()
        self._keyfile_entry = ttk.Entry(key_inner, textvariable=self._keyfile_var,
                                          state=tk.DISABLED)
        self._keyfile_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._browse_btn = ttk.Button(key_inner, text="浏览", style="TButton",
                                        command=self._browse_key, state=tk.DISABLED)
        self._browse_btn.pack(side=tk.RIGHT, padx=(4, 0))

        auth_frame.columnconfigure(0, weight=1)

        # ── 底部按钮 ──
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=pad_x, pady=(16, pad_y))

        self._test_btn = ttk.Button(btn_frame, text="测试连接", style="TButton",
                    command=self._test_connection)
        self._test_btn.pack(side=tk.LEFT)

        ttk.Button(btn_frame, text="取消", style="TButton",
                    command=self.destroy).pack(side=tk.RIGHT, padx=(8, 0))

        ttk.Button(btn_frame, text="确定", style="Primary.TButton",
                    command=self._on_ok).pack(side=tk.RIGHT)

    def _load_initial(self):
        """加载初始配置。"""
        if self._initial:
            self._name_var.set(self._initial.get("name", ""))
            self._host_var.set(self._initial.get("host", ""))
            self._port_var.set(self._initial.get("port", 22))
            self._username_var.set(self._initial.get("username", ""))
            if self._initial.get("key_file"):
                self._auth_mode.set("keyfile")
                self._keyfile_var.set(self._initial.get("key_file", ""))
                self._toggle_auth()

    def _toggle_auth(self):
        """切换认证方式时更新 UI 状态。"""
        is_key = self._auth_mode.get() == "keyfile"
        state = tk.DISABLED if is_key else tk.NORMAL
        self._password_var.set("") if is_key else self._password_var.get()
        key_state = tk.NORMAL if is_key else tk.DISABLED
        self._keyfile_entry.config(state=key_state)
        self._browse_btn.config(state=key_state)

    def _browse_key(self):
        """选择密钥文件。"""
        path = filedialog.askopenfilename(title="选择私钥文件",
                                            filetypes=[("所有文件", "*.*")])
        if path:
            self._keyfile_var.set(path)

    def _test_connection(self):
        """测试连接。"""
        config = self._build_config()
        if not config["host"] or not config["username"]:
            messagebox.showwarning("提示", "请填写服务器地址和用户名后再测试连接。")
            return
        if self._auth_mode.get() == "password" and not config["password"]:
            messagebox.showwarning("提示", "请填写密码后再测试连接。")
            return
        if self._auth_mode.get() == "keyfile" and not config["key_file"]:
            messagebox.showwarning("提示", "请选择私钥文件后再测试连接。")
            return

        # 禁用测试按钮，防止重复点击
        self._test_btn.config(state=tk.DISABLED, text="测试中...")

        def _test_task():
            from core.ssh_manager import SSHManager
            ssh = SSHManager()
            try:
                ssh.connect(
                    host=config["host"],
                    port=config["port"],
                    username=config["username"],
                    password=config.get("password"),
                    key_file=config.get("key_file"),
                )
                ssh.disconnect()
                return True, "连接成功"
            except Exception as e:
                return False, str(e)

        def _on_result(success, message):
            self._test_btn.config(state=tk.NORMAL, text="测试连接")
            if success:
                messagebox.showinfo("测试成功", f"成功连接到 {config['host']}:{config['port']}")
            else:
                messagebox.showerror("测试失败", f"连接失败: {message}")

        def _run_test():
            success, message = _test_task()
            self.after(0, lambda: _on_result(success, message))

        threading.Thread(target=_run_test, daemon=True).start()

    def _build_config(self) -> dict:
        """构建配置字典。"""
        return {
            "name": self._name_var.get().strip(),
            "host": self._host_var.get().strip(),
            "port": self._port_var.get(),
            "username": self._username_var.get().strip(),
            "password": self._password_var.get() if self._auth_mode.get() == "password" else None,
            "key_file": self._keyfile_var.get().strip() if self._auth_mode.get() == "keyfile" else None,
            "save_password": self._save_password_var.get(),
        }

    def _on_ok(self):
        """确定按钮处理。"""
        config = self._build_config()
        if not config["name"]:
            messagebox.showwarning("提示", "请填写连接名称。")
            return
        if not config["host"]:
            messagebox.showwarning("提示", "请填写服务器地址。")
            return
        if not config["username"]:
            messagebox.showwarning("提示", "请填写用户名。")
            return
        if self._auth_mode.get() == "password" and not config["password"]:
            messagebox.showwarning("提示", "请选择认证方式并填写密码。")
            return
        if self._auth_mode.get() == "keyfile" and not config["key_file"]:
            messagebox.showwarning("提示", "请选择私钥文件路径。")
            return

        self._result = config
        self.destroy()

    def get_result(self) -> dict | None:
        """获取对话框结果（关闭后调用）。"""
        return self._result
