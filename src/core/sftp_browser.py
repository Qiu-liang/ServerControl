"""
SFTP 目录浏览器
==============
封装 paramiko SFTP 操作，提供目录列举功能。
"""
import stat
import logging
from typing import List, Dict, Optional

import paramiko

logger = logging.getLogger(__name__)


class SFTPBrowser:
    """
    SFTP 目录浏览器。

    使用方式:
        browser = SFTPBrowser(ssh_client)
        items = browser.list_dir("/home/deploy")
        # items = [{"name": "app", "is_dir": True, "path": "/home/deploy/app"}, ...]
    """

    def __init__(self, ssh_client: paramiko.SSHClient):
        self._sftp: Optional[paramiko.SFTPClient] = None
        self._ssh_client = ssh_client

    def _ensure_sftp(self):
        """确保 SFTP 会话已打开。"""
        if self._sftp is None:
            self._sftp = self._ssh_client.open_sftp()
            logger.info("SFTP 会话已打开")

    def close(self):
        """关闭 SFTP 会话。"""
        if self._sftp is not None:
            try:
                self._sftp.close()
            except Exception as e:
                logger.warning("关闭 SFTP 会话时出错: %s", e)
            finally:
                self._sftp = None

    def list_dir(self, path: str) -> List[Dict]:
        """
        列举指定目录下的子目录（只返回目录，不返回文件）。

        参数:
            path: 远程目录的绝对路径

        返回:
            目录列表，每项包含:
            {
                "name": "子目录名",
                "is_dir": True,
                "path": "/完整/路径/子目录名"
            }
            按名称字母排序
        """
        self._ensure_sftp()

        items = []
        try:
            attrs_list = self._sftp.listdir_attr(path)
        except PermissionError:
            logger.warning("无权限列举目录: %s", path)
            return []
        except FileNotFoundError:
            logger.warning("目录不存在: %s", path)
            return []

        for attr in attrs_list:
            # 只保留目录
            if stat.S_ISDIR(attr.st_mode):
                name = attr.filename
                # 跳过隐藏目录和特殊目录
                if name.startswith(".") or name in ("..", "."):
                    continue
                full_path = f"{path.rstrip('/')}/{name}"
                items.append({
                    "name": name,
                    "is_dir": True,
                    "path": full_path,
                })

        # 按名称排序
        items.sort(key=lambda x: x["name"].lower())
        logger.info("列举目录 %s: %d 个子目录", path, len(items))
        return items

    def get_home_dir(self) -> str:
        """获取当前用户的 home 目录路径。"""
        self._ensure_sftp()
        # SFTP normalize 空字符串返回 home 目录
        try:
            home = self._sftp.normalize("")
            logger.info("Home 目录: %s", home)
            return home
        except Exception:
            return "/home"

    def exists(self, path: str) -> bool:
        """检查远程路径是否存在。"""
        self._ensure_sftp()
        try:
            self._sftp.stat(path)
            return True
        except FileNotFoundError:
            return False
