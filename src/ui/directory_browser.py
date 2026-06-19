"""
远程目录浏览器
=============
使用 tkinter Treeview 显示远程服务器目录结构。
支持懒加载子目录、路径导航、选中路径回调。
"""
import tkinter as tk
from tkinter import ttk
import logging

from ui.styles import (
    COLOR_PRIMARY, COLOR_TEXT_SECONDARY, FONT_NORMAL, FONT_SECTION
)

logger = logging.getLogger(__name__)


class DirectoryBrowser(ttk.Frame):
    """
    远程目录浏览器组件。

    功能:
        - Treeview 显示远程目录树
        - 懒加载子目录（点击展开时加载）
        - 路径显示栏 + 刷新按钮
        - 选中路径回调
    """

    def __init__(self, parent, on_path_selected=None, on_expand_dir=None):
        """
        参数:
            parent: 父组件
            on_path_selected: 路径被选中时的回调，接收路径字符串
            on_expand_dir: 目录展开时的回调，接收 (item_id, path)，
                           需调用 set_children() 填充子项
        """
        super().__init__(parent)
        self._on_path_selected = on_path_selected
        self._on_expand = on_expand_dir
        self._connected = False
        self._item_paths = {}  # item_id -> 远程路径映射
        self._init_ui()

    def _init_ui(self):
        # 头部
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=4, pady=(4, 2))

        ttk.Label(header, text="目录浏览", style="Section.TLabel").pack(side=tk.LEFT)

        # 刷新按钮
        refresh_btn = ttk.Button(header, text="刷新", style="TButton",
                                  command=self._on_refresh)
        refresh_btn.pack(side=tk.RIGHT)

        # 当前路径显示
        path_frame = ttk.Frame(self)
        path_frame.pack(fill=tk.X, padx=4, pady=2)

        ttk.Label(path_frame, text="路径:", style="TLabel").pack(side=tk.LEFT)
        self._path_var = tk.StringVar(value="/")
        self._path_entry = ttk.Entry(path_frame, textvariable=self._path_var,
                                      font=("Consolas", 9))
        self._path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        self._path_entry.bind("<Return>", self._on_path_enter)

        # Treeview 目录树
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree = ttk.Treeview(
            tree_frame,
            show="tree",
            selectmode="browse",
            yscrollcommand=scrollbar.set
        )
        self._tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._tree.yview)

        # 绑定事件
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<<TreeviewOpen>>", self._on_open)

    def set_connected(self, connected: bool):
        """设置连接状态。"""
        self._connected = connected
        if not connected:
            self.clear()

    def clear(self):
        """清空目录树。"""
        self._tree.delete(*self._tree.get_children())
        self._item_paths.clear()
        self._path_var.set("/")

    def load_root(self, root_path: str, entries: list):
        """
        加载根目录内容。

        参数:
            root_path: 根路径，如 "/" 或 "/home/user"
            entries: [(name, is_dir), ...] 列表
        """
        self.clear()
        self._path_var.set(root_path)
        self._add_entries("", root_path, entries)

    def set_children(self, parent_item: str, entries: list):
        """
        设置某个目录节点的子项。

        参数:
            parent_item: 父节点 item_id
            entries: [(name, is_dir), ...] 列表
        """
        # 移除旧的占位符
        for child in self._tree.get_children(parent_item):
            self._tree.delete(child)
        parent_path = self._item_paths.get(parent_item, "")
        self._add_entries(parent_item, parent_path, entries)

    def _add_entries(self, parent_item: str, parent_path: str, entries: list):
        """向指定父节点添加条目。"""
        # 排序：目录在前，文件在后
        entries = sorted(entries, key=lambda e: (not e[1], e[0].lower()))
        for name, is_dir in entries:
            display = name + "/" if is_dir else name
            item_id = self._tree.insert(
                parent_item, tk.END,
                text=display,
                values=("dir" if is_dir else "file",),
                open=False
            )
            if parent_path.endswith("/"):
                full_path = parent_path + name
            else:
                full_path = parent_path + "/" + name
            self._item_paths[item_id] = full_path

            # 目录添加占位子节点（使其可展开）
            if is_dir:
                self._tree.insert(item_id, tk.END, text="加载中...")

    def _on_select(self, event):
        """节点选中事件。"""
        sel = self._tree.selection()
        if not sel:
            return
        item_id = sel[0]
        path = self._item_paths.get(item_id, "")
        if path and self._on_path_selected:
            self._path_var.set(path)
            self._on_path_selected(path)

    def _on_open(self, event):
        """节点展开事件（懒加载）。"""
        item_id = self._tree.focus()
        if not item_id:
            return
        path = self._item_paths.get(item_id, "")
        values = self._tree.item(item_id, "values")
        if not values or values[0] != "dir":
            return
        if self._on_expand:
            self._on_expand(item_id, path)

    def _on_path_enter(self, event):
        """回车键触发路径跳转。"""
        path = self._path_var.get().strip()
        if path and self._on_expand:
            # 触发加载
            self._on_expand(None, path)

    def _on_refresh(self):
        """刷新按钮点击。"""
        path = self._path_var.get().strip() or "/"
        if self._on_expand and self._connected:
            self._on_expand(None, path)

    def get_selected_path(self) -> str:
        """获取当前选中的路径。"""
        return self._path_var.get()
