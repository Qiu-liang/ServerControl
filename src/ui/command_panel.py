"""
命令面板
========
显示预设命令按钮，点击触发执行。
使用 tkinter Frame + Button 实现按钮网格布局。
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging

from ui.styles import (
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_PRIMARY_LIGHT,
    COLOR_BG_WHITE, COLOR_BORDER, COLOR_TEXT, COLOR_TEXT_SECONDARY,
    COLOR_DISABLED_BG, FONT_NORMAL, FONT_BOLD, FONT_SMALL
)

logger = logging.getLogger(__name__)


class CommandPanel(ttk.Frame):
    """
    命令按钮面板组件。

    功能:
        - 按分类显示预设命令按钮
        - 按钮带文字描述，点击发出回调
        - 连接/断开状态控制按钮可用性
    """

    def __init__(self, parent, on_command_selected=None):
        """
        参数:
            parent: 父组件
            on_command_selected: 命令被选中时的回调，接收命令字典
        """
        super().__init__(parent)
        self._on_selected = on_command_selected
        self._connected = False
        self._cmd_buttons = []
        self._init_ui()

    def _init_ui(self):
        # 标题栏
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=4, pady=(4, 2))

        ttk.Label(header, text="命令面板", style="Section.TLabel").pack(side=tk.LEFT)

        self._status_label = ttk.Label(header, text="[未连接]",
                                        style="Disconnected.TLabel")
        self._status_label.pack(side=tk.RIGHT)

        # 可滚动命令区域
        self._scroll_canvas = tk.Canvas(self, bg=COLOR_BG_WHITE, highlightthickness=0)
        self._scroll_frame = ttk.Frame(self._scroll_canvas)
        self._scroll_window = self._scroll_canvas.create_window(
            (0, 0), window=self._scroll_frame, anchor=tk.NW
        )

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL,
                                   command=self._scroll_canvas.yview)
        self._scroll_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        self._scroll_frame.bind("<Configure>", self._on_frame_configure)
        self._scroll_canvas.bind("<Configure>", self._on_canvas_configure)
        # 绑定鼠标滚轮（只在命令面板内生效）
        self._scroll_canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_frame_configure(self, event):
        self._scroll_canvas.configure(scrollregion=self._scroll_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._scroll_canvas.itemconfig(self._scroll_window, width=event.width)

    def _on_mousewheel(self, event):
        self._scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_commands(self, categories: dict):
        """
        加载命令到面板。

        参数:
            categories: {分类名: [命令字典列表]} 的字典
        """
        # 清空旧按钮
        for w in self._scroll_frame.winfo_children():
            w.destroy()
        self._cmd_buttons.clear()

        row = 0
        for cat_name, commands in categories.items():
            # 分类标题
            cat_label = ttk.Label(self._scroll_frame, text=f"-- {cat_name} --",
                                   style="Secondary.TLabel")
            cat_label.grid(row=row, column=0, columnspan=2, sticky=tk.W,
                           padx=8, pady=(12, 4))
            row += 1

            # 命令按钮网格
            col = 0
            for cmd in commands:
                btn = tk.Button(
                    self._scroll_frame,
                    text=cmd.get('name', '未知'),
                    bg=COLOR_BG_WHITE, fg=COLOR_TEXT,
                    activebackground=COLOR_PRIMARY_LIGHT,
                    activeforeground=COLOR_PRIMARY,
                    font=FONT_BOLD,
                    relief=tk.SOLID, bd=1,
                    padx=16, pady=10,
                    cursor="hand2",
                    command=lambda c=cmd: self._on_click(c)
                )
                btn.grid(row=row, column=col, padx=4, pady=4, sticky=tk.EW,
                         ipadx=4, ipady=2)
                self._cmd_buttons.append(btn)
                col += 1
                if col >= 2:
                    col = 0
                    row += 1

            if col != 0:
                row += 1

        # 列等宽
        for i in range(2):
            self._scroll_frame.columnconfigure(i, weight=1)

    def _on_click(self, cmd: dict):
        """按钮点击处理。"""
        if not self._connected:
            messagebox.showwarning("提示", "请先连接服务器后再执行命令。")
            return
        if self._on_selected:
            self._on_selected(cmd)

    def set_connected(self, connected: bool):
        """设置连接状态，控制按钮可用性。"""
        self._connected = connected
        state = tk.NORMAL if connected else tk.DISABLED
        for btn in self._cmd_buttons:
            btn.config(state=state)
        if connected:
            self._status_label.config(text="[已连接]", style="Connected.TLabel")
        else:
            self._status_label.config(text="[未连接]", style="Disconnected.TLabel")
