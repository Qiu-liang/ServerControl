"""
会话管理器
==========
显示历史登录过的会话，支持重新连接、编辑和删除。
上下分栏布局：上方显示会话名称列表，下方显示选中会话的详细信息。
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime

from ui.styles import (
    COLOR_PRIMARY, COLOR_TEXT_SECONDARY, FONT_NORMAL, FONT_SECTION
)
from security.credential_store import CredentialStore

logger = logging.getLogger(__name__)


class SessionManager(ttk.Frame):
    """
    会话管理器组件。

    功能:
        - 上半部分：Treeview 显示会话名称列表
        - 下半部分：显示选中会话的详细信息
        - 支持双击或右键菜单连接会话
        - 支持删除会话历史记录
        - 支持编辑会话配置
        - 提供刷新按钮
    """

    def __init__(self, parent, on_session_connect=None, on_session_edit=None):
        """
        参数:
            parent: 父组件
            on_session_connect: 会话连接回调，接收会话配置字典
            on_session_edit: 会话编辑回调，接收会话配置字典
        """
        super().__init__(parent)
        self._on_session_connect = on_session_connect
        self._on_session_edit = on_session_edit
        self._credential_store = CredentialStore()
        self._sessions = []  # 存储会话历史记录
        self._selected_session = None  # 当前选中的会话
        self._init_ui()
        self._load_sessions()

    def _init_ui(self):
        # 头部：标题和刷新按钮
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=4, pady=(4, 0))

        ttk.Label(header, text="会话管理器", style="Section.TLabel").pack(side=tk.LEFT)

        # 刷新按钮
        refresh_btn = ttk.Button(header, text="刷新", style="TButton",
                                  command=self._on_refresh)
        refresh_btn.pack(side=tk.RIGHT)

        # 使用PanedWindow分割上下区域
        paned_window = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 4))

        # ── 上半部分：会话名称列表 ──
        top_frame = ttk.Frame(paned_window)
        paned_window.add(top_frame, weight=2)

        # Treeview 会话名称列表
        tree_frame = ttk.Frame(top_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 只显示会话名称列
        self._tree = ttk.Treeview(
            tree_frame,
            columns=("name",),
            show="headings",
            selectmode="browse",
            yscrollcommand=scrollbar.set
        )
        
        # 设置列标题
        self._tree.heading("name", text="会话名称")
        
        # 设置列宽
        self._tree.column("name", width=200, minwidth=150)
        
        self._tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._tree.yview)

        # 绑定事件
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Button-3>", self._on_right_click)  # 右键菜单

        # 创建右键菜单
        self._context_menu = tk.Menu(self, tearoff=0)
        self._context_menu.add_command(label="连接", command=self._on_connect_selected)
        self._context_menu.add_command(label="编辑", command=self._on_edit_selected)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="删除", command=self._on_delete_selected)

        # 空状态提示
        self._empty_label = ttk.Label(
            tree_frame, 
            text="暂无历史会话记录",
            style="Secondary.TLabel",
            justify=tk.CENTER
        )
        self._empty_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # ── 下半部分：会话详细信息 ──
        bottom_frame = ttk.Frame(paned_window)
        paned_window.add(bottom_frame, weight=1)

        # 详细信息标题
        detail_header = ttk.Frame(bottom_frame)
        detail_header.pack(fill=tk.X, padx=4, pady=(4, 2))
        ttk.Label(detail_header, text="会话详情", style="Section.TLabel").pack(side=tk.LEFT)

        # 详细信息内容
        detail_content = ttk.Frame(bottom_frame)
        detail_content.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        # 使用标签显示详细信息
        self._detail_name_var = tk.StringVar(value="名称: ")
        self._detail_host_var = tk.StringVar(value="主机: ")
        self._detail_port_var = tk.StringVar(value="端口: ")
        self._detail_username_var = tk.StringVar(value="用户名: ")
        self._detail_last_connect_var = tk.StringVar(value="最后连接: ")
        self._detail_status_var = tk.StringVar(value="状态: ")
        self._detail_connect_count_var = tk.StringVar(value="连接次数: ")

        # 创建详细信息标签
        ttk.Label(detail_content, textvariable=self._detail_name_var, 
                  font=FONT_NORMAL).pack(anchor=tk.W, pady=1)
        ttk.Label(detail_content, textvariable=self._detail_host_var,
                  font=FONT_NORMAL).pack(anchor=tk.W, pady=1)
        ttk.Label(detail_content, textvariable=self._detail_port_var,
                  font=FONT_NORMAL).pack(anchor=tk.W, pady=1)
        ttk.Label(detail_content, textvariable=self._detail_username_var,
                  font=FONT_NORMAL).pack(anchor=tk.W, pady=1)
        ttk.Label(detail_content, textvariable=self._detail_last_connect_var,
                  font=FONT_NORMAL).pack(anchor=tk.W, pady=1)
        ttk.Label(detail_content, textvariable=self._detail_status_var,
                  font=FONT_NORMAL).pack(anchor=tk.W, pady=1)
        ttk.Label(detail_content, textvariable=self._detail_connect_count_var,
                  font=FONT_NORMAL).pack(anchor=tk.W, pady=1)

    def _load_sessions(self):
        """加载会话历史记录。"""
        try:
            self._sessions = self._credential_store.get_session_history()
            self._update_treeview()
        except Exception as e:
            logger.error("加载会话历史失败: %s", e)
            self._sessions = []

    def _update_treeview(self):
        """更新Treeview显示。"""
        # 清空现有项目
        for item in self._tree.get_children():
            self._tree.delete(item)
        
        # 显示/隐藏空状态提示
        if not self._sessions:
            self._empty_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        else:
            self._empty_label.place_forget()
        
        # 添加会话记录（只显示名称）
        for session in self._sessions:
            self._tree.insert("", tk.END, values=(session.get("name", ""),))

    def _on_select(self, event):
        """选择事件处理。"""
        selection = self._tree.selection()
        if not selection:
            self._clear_detail()
            return
        
        item = selection[0]
        values = self._tree.item(item, "values")
        if not values:
            self._clear_detail()
            return
        
        # 根据名称查找会话记录
        session_name = values[0]
        for session in self._sessions:
            if session.get("name") == session_name:
                self._selected_session = session
                self._update_detail(session)
                return
        
        self._clear_detail()

    def _update_detail(self, session: dict):
        """更新详细信息显示。"""
        self._detail_name_var.set(f"名称: {session.get('name', '')}")
        self._detail_host_var.set(f"主机: {session.get('host', '')}")
        self._detail_port_var.set(f"端口: {session.get('port', 22)}")
        self._detail_username_var.set(f"用户名: {session.get('username', '')}")
        
        # 格式化最后连接时间
        last_connect = session.get("last_connect_time", "")
        if last_connect:
            try:
                dt = datetime.fromisoformat(last_connect)
                last_connect_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                last_connect_str = last_connect
        else:
            last_connect_str = "未知"
        self._detail_last_connect_var.set(f"最后连接: {last_connect_str}")
        
        # 状态显示
        status = "成功" if session.get("success", False) else "失败"
        self._detail_status_var.set(f"状态: {status}")
        
        # 连接次数
        connect_count = session.get("connect_count", 0)
        self._detail_connect_count_var.set(f"连接次数: {connect_count}")

    def _clear_detail(self):
        """清空详细信息显示。"""
        self._detail_name_var.set("名称: ")
        self._detail_host_var.set("主机: ")
        self._detail_port_var.set("端口: ")
        self._detail_username_var.set("用户名: ")
        self._detail_last_connect_var.set("最后连接: ")
        self._detail_status_var.set("状态: ")
        self._detail_connect_count_var.set("连接次数: ")



    def _on_refresh(self):
        """刷新按钮点击。"""
        self._load_sessions()

    def _on_double_click(self, event):
        """双击事件处理。"""
        self._on_connect_selected()

    def _on_right_click(self, event):
        """右键菜单事件处理。"""
        # 选中右键点击的项目
        item = self._tree.identify_row(event.y)
        if item:
            self._tree.selection_set(item)
            self._context_menu.post(event.x_root, event.y_root)

    def _get_selected_session(self):
        """获取当前选中的会话。"""
        return self._selected_session

    def _on_connect_selected(self):
        """连接选中的会话。"""
        session = self._get_selected_session()
        if not session:
            messagebox.showwarning("提示", "请先选择一个会话。")
            return
        
        if self._on_session_connect:
            self._on_session_connect(session)

    def _on_edit_selected(self):
        """编辑选中的会话。"""
        session = self._get_selected_session()
        if not session:
            messagebox.showwarning("提示", "请先选择一个会话。")
            return
        
        if self._on_session_edit:
            self._on_session_edit(session)

    def _on_delete_selected(self):
        """删除选中的会话。"""
        session = self._get_selected_session()
        if not session:
            messagebox.showwarning("提示", "请先选择一个会话。")
            return
        
        session_name = session.get("name", "")
        if messagebox.askyesno("确认删除", f"确定要删除会话 '{session_name}' 的历史记录吗？"):
            try:
                self._credential_store.delete_session_history(session_name)
                self._load_sessions()  # 重新加载
                self._clear_detail()
                self._selected_session = None
                logger.info("会话历史已删除: %s", session_name)
            except Exception as e:
                logger.error("删除会话历史失败: %s", e)
                messagebox.showerror("错误", f"删除会话历史失败: {e}")

    def refresh(self):
        """公共方法：刷新会话列表。"""
        self._load_sessions()

    def add_session(self, name: str, config: dict, success: bool = True):
        """
        添加会话记录。
        
        参数:
            name: 会话名称
            config: 连接配置
            success: 连接是否成功
        """
        try:
            self._credential_store.save_session_history(name, config, success)
            self._load_sessions()  # 重新加载
        except Exception as e:
            logger.error("保存会话历史失败: %s", e)
