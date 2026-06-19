"""
Tkinter 主题与样式配置
=====================
定义全局颜色、字体常量和 ttk 样式配置。
"""
import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)

# ── 颜色常量 ──────────────────────────────────────────────────────────────────
COLOR_PRIMARY = "#3B82F6"       # 主色调：蓝色
COLOR_PRIMARY_HOVER = "#2563EB"
COLOR_PRIMARY_LIGHT = "#EFF6FF"
COLOR_SUCCESS = "#10B981"       # 成功/在线：绿色
COLOR_ERROR = "#EF4444"         # 错误/危险：红色
COLOR_WARNING = "#F59E0B"       # 警告：琥珀色
COLOR_BG = "#F0F2F5"            # 主背景
COLOR_BG_WHITE = "#FFFFFF"      # 卡片/面板背景
COLOR_TEXT = "#1F2937"          # 主文本
COLOR_TEXT_SECONDARY = "#64748B"  # 次要文本
COLOR_BORDER = "#E2E8F0"        # 边框色
COLOR_DISABLED_BG = "#CBD5E1"   # 禁用背景
COLOR_DISABLED_TEXT = "#94A3B8" # 禁用文本

# ── 控制台颜色 ────────────────────────────────────────────────────────────────
CONSOLE_BG = "#0F172A"
CONSOLE_FG = "#E2E8F0"
CONSOLE_INFO = "#60A5FA"
CONSOLE_SUCCESS = "#34D399"
CONSOLE_ERROR = "#EF4444"

# ── 字体 ──────────────────────────────────────────────────────────────────────
FONT_FAMILY = "Microsoft YaHei UI"
FONT_NORMAL = (FONT_FAMILY, 10)
FONT_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_TITLE = (FONT_FAMILY, 12, "bold")
FONT_SECTION = (FONT_FAMILY, 11, "bold")
FONT_CONSOLE = ("Consolas", 10)


def apply_theme(root: tk.Tk) -> None:
    """
    配置 ttk 全局样式主题。

    参数:
        root: tkinter 根窗口
    """
    root.configure(bg=COLOR_BG)

    style = ttk.Style(root)
    style.theme_use("clam")  # clam 主题最接近现代风格，易于定制

    # ── 全局 Frame ──
    style.configure("TFrame", background=COLOR_BG)
    style.configure("Card.TFrame", background=COLOR_BG_WHITE)

    # ── 标签 ──
    style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                     font=FONT_NORMAL)
    style.configure("Card.TLabel", background=COLOR_BG_WHITE)
    style.configure("Title.TLabel", font=FONT_TITLE, foreground=COLOR_TEXT)
    style.configure("Section.TLabel", font=FONT_SECTION, foreground=COLOR_PRIMARY)
    style.configure("Secondary.TLabel", foreground=COLOR_TEXT_SECONDARY,
                     font=FONT_SMALL)
    style.configure("Status.TLabel", font=FONT_NORMAL)
    style.configure("Connected.TLabel", foreground=COLOR_SUCCESS, font=FONT_BOLD)
    style.configure("Disconnected.TLabel", foreground=COLOR_TEXT_SECONDARY)
    style.configure("Connecting.TLabel", foreground=COLOR_WARNING, font=FONT_NORMAL)

    # ── 按钮 ──
    style.configure("TButton", font=FONT_NORMAL, padding=(16, 8))
    style.configure("Primary.TButton", background=COLOR_PRIMARY,
                     foreground="white", font=FONT_BOLD)
    style.map("Primary.TButton",
              background=[("active", COLOR_PRIMARY_HOVER),
                          ("disabled", COLOR_DISABLED_BG)])
    style.configure("Danger.TButton", background=COLOR_ERROR,
                     foreground="white", font=FONT_BOLD)
    style.map("Danger.TButton",
              background=[("active", "#DC2626"),
                          ("disabled", COLOR_DISABLED_BG)])
    style.configure("Success.TButton", background=COLOR_SUCCESS,
                     foreground="white", font=FONT_BOLD)
    style.map("Success.TButton",
              background=[("active", "#059669"),
                          ("disabled", COLOR_DISABLED_BG)])

    # ── 输入框 ──
    style.configure("TEntry", padding=(10, 8), font=FONT_NORMAL)

    # ── 下拉框 ──
    style.configure("TCombobox", padding=(10, 8), font=FONT_NORMAL)

    # ── 单选按钮 ──
    style.configure("TRadiobutton", font=FONT_NORMAL, padding=(4, 4))

    # ── 分组框 ──
    style.configure("TLabelframe", background=COLOR_BG_WHITE,
                     relief="solid", borderwidth=1)
    style.configure("TLabelframe.Label", background=COLOR_BG_WHITE,
                     foreground=COLOR_PRIMARY, font=FONT_BOLD)

    # ── 进度条 ──
    style.configure("blue.Horizontal.TProgressbar",
                     troughcolor=COLOR_BORDER, background=COLOR_PRIMARY,
                     thickness=6)

    # ── 分隔线 ──
    style.configure("TSeparator", background=COLOR_BORDER)

    # ── Notebook（用于向导分页） ──
    style.configure("TNotebook", background=COLOR_BG)
    style.configure("TNotebook.Tab", padding=(20, 8), font=FONT_NORMAL)

    # ── Treeview ──
    style.configure("Treeview", font=FONT_NORMAL, rowheight=28,
                     background=COLOR_BG_WHITE, fieldbackground=COLOR_BG_WHITE)
    style.configure("Treeview.Heading", font=FONT_BOLD)
    style.map("Treeview",
              background=[("selected", COLOR_PRIMARY_LIGHT)],
              foreground=[("selected", COLOR_PRIMARY)])

    # ── Scrollbar ──
    style.configure("TScrollbar", troughcolor=COLOR_BG,
                     background=COLOR_DISABLED_BG, width=10)

    logger.info("Tkinter 主题已应用")
