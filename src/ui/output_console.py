"""
命令输出控制台
=============
实时显示命令执行输出，支持错误高亮、自动滚动。
使用 tkinter Text 组件实现深色终端风格。
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

from ui.styles import (
    CONSOLE_BG, CONSOLE_FG, CONSOLE_INFO, CONSOLE_SUCCESS, CONSOLE_ERROR,
    FONT_CONSOLE, FONT_NORMAL, FONT_BOLD, COLOR_TEXT, COLOR_BG, COLOR_BORDER,
    COLOR_PRIMARY, COLOR_TEXT_SECONDARY
)


class OutputConsole(ttk.Frame):
    """
    命令输出控制台组件。

    功能:
        - 实时显示命令输出（流式）
        - 错误输出红色高亮
        - 自动滚动到底部
        - 复制、清空操作
    """

    MAX_LINES = 5000  # 最大保留行数

    def __init__(self, parent):
        super().__init__(parent)
        self._line_count = 0
        self._init_ui()

    def _init_ui(self):
        # 头部标题栏
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=4, pady=(4, 2))

        ttk.Label(header, text="输出控制台", style="Section.TLabel").pack(side=tk.LEFT)

        # 右侧按钮
        btn_frame = ttk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)

        copy_btn = ttk.Button(btn_frame, text="复制", style="TButton",
                               command=self._copy_selected)
        copy_btn.pack(side=tk.LEFT, padx=2)

        clear_btn = ttk.Button(btn_frame, text="清空", style="TButton",
                                command=self.clear)
        clear_btn.pack(side=tk.LEFT, padx=2)

        # 输出文本区域（深色背景）
        text_frame = ttk.Frame(self, style="Card.TFrame")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._text = tk.Text(
            text_frame,
            bg=CONSOLE_BG, fg=CONSOLE_FG,
            font=FONT_CONSOLE,
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            padx=8, pady=8,
            yscrollcommand=scrollbar.set,
            insertbackground=CONSOLE_FG,
            selectbackground=COLOR_PRIMARY,
            selectforeground="white"
        )
        self._text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self._text.yview)

        # 文本标签（用于颜色）
        self._text.tag_configure("normal", foreground=CONSOLE_FG)
        self._text.tag_configure("error", foreground=CONSOLE_ERROR, font=(FONT_CONSOLE[0], FONT_CONSOLE[1], "bold"))
        self._text.tag_configure("info", foreground=CONSOLE_INFO, font=(FONT_CONSOLE[0], FONT_CONSOLE[1], "bold"))
        self._text.tag_configure("success", foreground=CONSOLE_SUCCESS, font=(FONT_CONSOLE[0], FONT_CONSOLE[1], "bold"))
        self._text.tag_configure("header", foreground=CONSOLE_INFO, font=(FONT_CONSOLE[0], FONT_CONSOLE[1], "bold"))
        self._text.tag_configure("separator", foreground="#475569")

    def _append(self, text: str, tag: str = "normal"):
        """向控制台追加带标签的文本。"""
        self._text.config(state=tk.NORMAL)
        self._text.insert(tk.END, text + "\n", tag)
        self._text.config(state=tk.DISABLED)
        self._text.see(tk.END)
        self._line_count += 1
        self._trim_if_needed()

    def _trim_if_needed(self):
        """超过最大行数时裁剪旧内容。"""
        if self._line_count > self.MAX_LINES:
            self._text.config(state=tk.NORMAL)
            lines_to_remove = self._line_count - self.MAX_LINES
            self._text.delete("1.0", f"{lines_to_remove + 1}.0")
            self._text.config(state=tk.DISABLED)
            self._line_count = self.MAX_LINES

    def append_output(self, text: str, is_error: bool = False):
        """追加一行命令输出。"""
        self._append(text, "error" if is_error else "normal")

    def append_info(self, message: str):
        """追加一条带时间戳的信息（蓝色）。"""
        ts = datetime.now().strftime("%H:%M:%S")
        self._append(f"[{ts}] {message}", "info")

    def append_success(self, message: str):
        """追加一条成功消息（绿色）。"""
        ts = datetime.now().strftime("%H:%M:%S")
        self._append(f"[{ts}] {message}", "success")

    def append_command_header(self, command: str):
        """追加命令执行头部信息。"""
        ts = datetime.now().strftime("%H:%M:%S")
        self._text.config(state=tk.NORMAL)
        self._text.insert(tk.END, f"\n[{ts}] 执行命令: {command}\n", "header")
        self._text.insert(tk.END, "-" * 60 + "\n", "separator")
        self._text.config(state=tk.DISABLED)
        self._text.see(tk.END)

    def append_command_footer(self, exit_code: int):
        """追加命令执行结束信息。"""
        self._text.config(state=tk.NORMAL)
        self._text.insert(tk.END, "-" * 60 + "\n", "separator")
        if exit_code == 0:
            self._text.insert(tk.END, f"[命令执行完成 - 退出码: {exit_code}]\n", "success")
        else:
            self._text.insert(tk.END, f"[命令执行完成 - 退出码: {exit_code}]\n", "error")
        self._text.config(state=tk.DISABLED)
        self._text.see(tk.END)

    def clear(self):
        """清空控制台所有内容。"""
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.config(state=tk.DISABLED)
        self._line_count = 0

    def _copy_selected(self):
        """复制选中文本到剪贴板。"""
        try:
            text = self._text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self._text.clipboard_clear()
            self._text.clipboard_append(text)
        except tk.TclError:
            pass  # 没有选中文本
