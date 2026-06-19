"""
Tkinter 主题与样式配置
=====================
定义全局颜色、字体常量和 ttk 样式配置。
支持根据屏幕分辨率自动缩放。
"""
import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)

# ── 基准分辨率（设计时的参考分辨率） ─────────────────────────────────────────
BASE_SCREEN_WIDTH = 1920
BASE_SCREEN_HEIGHT = 1080

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

# ── 字体族 ────────────────────────────────────────────────────────────────────
FONT_FAMILY = "Microsoft YaHei UI"
FONT_CONSOLE_FAMILY = "Consolas"


# ── 动态字体缩放函数 ─────────────────────────────────────────────────────────
def get_scale_factor(screen_width: int, screen_height: int) -> float:
    """
    根据屏幕分辨率计算缩放比例。
    
    参数:
        screen_width: 屏幕宽度
        screen_height: 屏幕高度
    
    返回:
        缩放比例（相对于基准分辨率 1920x1080）
    """
    width_ratio = screen_width / BASE_SCREEN_WIDTH
    height_ratio = screen_height / BASE_SCREEN_HEIGHT
    return min(width_ratio, height_ratio)


def get_scaled_size(screen_width: int, screen_height: int, base_size: int, min_size: int = 9) -> int:
    """
    返回缩放后的字号大小。
    
    参数:
        screen_width: 屏幕宽度
        screen_height: 屏幕高度
        base_size: 基准字号
        min_size: 最小字号限制
    
    返回:
        缩放后的字号
    """
    scale = get_scale_factor(screen_width, screen_height)
    scaled = int(base_size * scale)
    return max(min_size, scaled)


def get_scaled_font(screen_width: int, screen_height: int, base_size: int, bold: bool = False) -> tuple:
    """
    返回缩放后的字体元组。
    
    参数:
        screen_width: 屏幕宽度
        screen_height: 屏幕高度
        base_size: 基准字号
        bold: 是否加粗
    
    返回:
        (字体族, 字号, ["bold"]) 字体元组
    """
    size = get_scaled_size(screen_width, screen_height, base_size)
    if bold:
        return (FONT_FAMILY, size, "bold")
    return (FONT_FAMILY, size)


def get_scaled_console_font(screen_width: int, screen_height: int, base_size: int = 10) -> tuple:
    """
    返回缩放后的控制台字体元组。
    """
    size = get_scaled_size(screen_width, screen_height, base_size)
    return (FONT_CONSOLE_FAMILY, size)


# 默认字体（未缩放，兼容旧代码）
FONT_NORMAL = (FONT_FAMILY, 10)
FONT_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_TITLE = (FONT_FAMILY, 12, "bold")
FONT_SECTION = (FONT_FAMILY, 11, "bold")
FONT_CONSOLE = (FONT_CONSOLE_FAMILY, 10)


def apply_theme(root: tk.Tk, screen_width: int = None, screen_height: int = None) -> None:
    """
    配置 ttk 全局样式主题。
    
    参数:
        root: tkinter 根窗口
        screen_width: 屏幕宽度（可选，用于字体缩放）
        screen_height: 屏幕高度（可选，用于字体缩放）
    """
    root.configure(bg=COLOR_BG)
    
    # 获取屏幕尺寸（如果未提供）
    if screen_width is None or screen_height is None:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
    
    # 计算缩放后的字体
    font_normal = get_scaled_font(screen_width, screen_height, 10)
    font_bold = get_scaled_font(screen_width, screen_height, 10, bold=True)
    font_small = get_scaled_font(screen_width, screen_height, 9)
    font_title = get_scaled_font(screen_width, screen_height, 12, bold=True)
    font_section = get_scaled_font(screen_width, screen_height, 11, bold=True)
    font_console = get_scaled_console_font(screen_width, screen_height, 10)
    
    # 计算缩放后的 padding 和 rowheight
    scale = get_scale_factor(screen_width, screen_height)
    padding_small = (int(16 * scale), int(8 * scale))
    padding_entry = (int(10 * scale), int(8 * scale))
    padding_tab = (int(20 * scale), int(8 * scale))
    rowheight = int(28 * scale)
    scrollbar_width = int(10 * scale)
    
    style = ttk.Style(root)
    style.theme_use("clam")  # clam 主题最接近现代风格，易于定制
    
    # ── 全局 Frame ──
    style.configure("TFrame", background=COLOR_BG)
    style.configure("Card.TFrame", background=COLOR_BG_WHITE)
    
    # ── 标签 ──
    style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                     font=font_normal)
    style.configure("Card.TLabel", background=COLOR_BG_WHITE)
    style.configure("Title.TLabel", font=font_title, foreground=COLOR_TEXT)
    style.configure("Section.TLabel", font=font_section, foreground=COLOR_PRIMARY)
    style.configure("Secondary.TLabel", foreground=COLOR_TEXT_SECONDARY,
                     font=font_small)
    style.configure("Status.TLabel", font=font_normal)
    style.configure("Connected.TLabel", foreground=COLOR_SUCCESS, font=font_bold)
    style.configure("Disconnected.TLabel", foreground=COLOR_TEXT_SECONDARY)
    style.configure("Connecting.TLabel", foreground=COLOR_WARNING, font=font_normal)
    
    # ── 按钮 ──
    style.configure("TButton", font=font_normal, padding=padding_small)
    style.configure("Primary.TButton", background=COLOR_PRIMARY,
                     foreground="white", font=font_bold)
    style.map("Primary.TButton",
              background=[("active", COLOR_PRIMARY_HOVER),
                          ("disabled", COLOR_DISABLED_BG)])
    style.configure("Danger.TButton", background=COLOR_ERROR,
                     foreground="white", font=font_bold)
    style.map("Danger.TButton",
              background=[("active", "#DC2626"),
                          ("disabled", COLOR_DISABLED_BG)])
    style.configure("Success.TButton", background=COLOR_SUCCESS,
                     foreground="white", font=font_bold)
    style.map("Success.TButton",
              background=[("active", "#059669"),
                          ("disabled", COLOR_DISABLED_BG)])
    
    # ── 输入框 ──
    style.configure("TEntry", padding=padding_entry, font=font_normal)
    
    # ── 下拉框 ──
    style.configure("TCombobox", padding=padding_entry, font=font_normal)
    
    # ── 单选按钮 ──
    style.configure("TRadiobutton", font=font_normal, padding=(int(4 * scale), int(4 * scale)))
    
    # ── 复选框 ──
    style.configure("TCheckbutton", font=font_normal, padding=(int(4 * scale), int(4 * scale)))
    
    # ── 分组框 ──
    style.configure("TLabelframe", background=COLOR_BG_WHITE,
                     relief="solid", borderwidth=1)
    style.configure("TLabelframe.Label", background=COLOR_BG_WHITE,
                     foreground=COLOR_PRIMARY, font=font_bold)
    
    # ── 进度条 ──
    style.configure("blue.Horizontal.TProgressbar",
                     troughcolor=COLOR_BORDER, background=COLOR_PRIMARY,
                     thickness=int(6 * scale))
    
    # ── 分隔线 ──
    style.configure("TSeparator", background=COLOR_BORDER)
    
    # ── Notebook（用于向导分页） ──
    style.configure("TNotebook", background=COLOR_BG)
    style.configure("TNotebook.Tab", padding=padding_tab, font=font_normal)
    
    # ── Treeview ──
    style.configure("Treeview", font=font_normal, rowheight=rowheight,
                     background=COLOR_BG_WHITE, fieldbackground=COLOR_BG_WHITE)
    style.configure("Treeview.Heading", font=font_bold)
    style.map("Treeview",
              background=[("selected", COLOR_PRIMARY_LIGHT)],
              foreground=[("selected", COLOR_PRIMARY)])
    
    # ── Scrollbar ──
    style.configure("TScrollbar", troughcolor=COLOR_BG,
                     background=COLOR_DISABLED_BG, width=scrollbar_width)
    
    logger.info("Tkinter 主题已应用 (缩放比例: %.2f)", get_scale_factor(screen_width, screen_height))
"""
Tkinter 主题与样式配置
=====================
定义全局颜色、字体常量和 ttk 样式配置。
支持根据屏幕分辨率自动缩放。
"""
import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)

# ── 基准分辨率（设计时的参考分辨率） ─────────────────────────────────────────
BASE_SCREEN_WIDTH = 1920
BASE_SCREEN_HEIGHT = 1080

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

# ── 字体族 ────────────────────────────────────────────────────────────────────
FONT_FAMILY = "Microsoft YaHei UI"
FONT_CONSOLE_FAMILY = "Consolas"


# ── 动态字体缩放函数 ─────────────────────────────────────────────────────────