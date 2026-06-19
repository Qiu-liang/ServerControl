"""
跨平台配置目录解析
==================
返回应用配置文件的存储路径（Windows: %APPDATA%/ServerControl）。
确保目录存在，不存在时自动创建。
"""
import os
import sys


def get_config_dir() -> str:
    """
    返回应用配置目录的绝对路径。
    Windows: C:\\Users\\<用户名>\\AppData\\Roaming\\ServerControl
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    config_dir = os.path.join(base, "ServerControl")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def get_encrypted_config_path() -> str:
    """返回加密连接配置文件的完整路径。"""
    return os.path.join(get_config_dir(), "connections.enc")


def get_log_path() -> str:
    """返回日志文件的完整路径。"""
    return os.path.join(get_config_dir(), "servercontrol.log")


def get_asset_path(*parts) -> str:
    """
    返回 assets 目录下资源的绝对路径。
    兼容 PyInstaller 打包后的路径（_MEIPASS）。
    """
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后，资源在 _MEIPASS 目录
        base = sys._MEIPASS
    else:
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..")
    return os.path.join(base, "assets", *parts)


def get_config_asset_path(*parts) -> str:
    """
    返回 config 目录下配置文件的绝对路径。
    兼容 PyInstaller 打包后的路径。
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..")
    return os.path.join(base, "config", *parts)
