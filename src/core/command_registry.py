"""
命令注册表
==========
加载 config/commands.json，按分类分组，提供给 UI 层渲染。
"""
import json
import logging
from typing import Dict, List

from utils.config_paths import get_config_asset_path

logger = logging.getLogger(__name__)


class CommandRegistry:
    """
    预设命令管理器。

    commands.json 格式:
    {
        "version": 1,
        "commands": [
            {
                "id": "start_service",
                "name": "启动服务",
                "description": "启动 Nginx + 后端应用服务",
                "icon": "start",
                "command": "sudo systemctl start nginx && sudo systemctl start myapp",
                "category": "服务管理",
                "confirm": true,
                "confirm_message": "确定要启动服务吗？"
            }
        ]
    }
    """

    def __init__(self):
        self._commands: List[Dict] = []
        self._categories: Dict[str, List[Dict]] = {}

    def load(self) -> None:
        """从 commands.json 加载预设命令。"""
        path = get_config_asset_path("commands.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._commands = data.get("commands", [])
            self._build_categories()
            logger.info("已加载 %d 条预设命令，%d 个分类",
                        len(self._commands), len(self._categories))
        except FileNotFoundError:
            logger.warning("命令配置文件不存在: %s，使用默认命令", path)
            self._commands = _DEFAULT_COMMANDS
            self._build_categories()
        except Exception as e:
            logger.error("加载命令配置失败: %s", e)
            self._commands = _DEFAULT_COMMANDS
            self._build_categories()

    def _build_categories(self) -> None:
        """按 category 字段对命令分组。"""
        self._categories = {}
        for cmd in self._commands:
            cat = cmd.get("category", "其他")
            if cat not in self._categories:
                self._categories[cat] = []
            self._categories[cat].append(cmd)

    def get_all_commands(self) -> List[Dict]:
        """返回所有命令列表。"""
        return self._commands

    def get_categories(self) -> Dict[str, List[Dict]]:
        """返回按分类分组的命令字典。"""
        return self._categories

    def get_command_by_id(self, cmd_id: str) -> Dict:
        """根据 ID 获取命令配置。"""
        for cmd in self._commands:
            if cmd.get("id") == cmd_id:
                return cmd
        return {}

    def save(self) -> None:
        """将当前命令列表保存回 commands.json。"""
        path = get_config_asset_path("commands.json")
        data = {"version": 1, "commands": self._commands}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("命令配置已保存: %s", path)
        except Exception as e:
            logger.error("保存命令配置失败: %s", e)


# ── 内置默认命令（commands.json 不存在时使用） ───────────────────────────────────
_DEFAULT_COMMANDS = [
    {
        "id": "start_service",
        "name": "启动服务",
        "description": "启动主要应用服务",
        "icon": "start",
        "command": "sudo systemctl start nginx",
        "category": "服务管理",
        "confirm": True,
        "confirm_message": "确定要启动服务吗？"
    },
    {
        "id": "stop_service",
        "name": "停止服务",
        "description": "停止主要应用服务",
        "icon": "stop",
        "command": "sudo systemctl stop nginx",
        "category": "服务管理",
        "confirm": True,
        "confirm_message": "停止服务将中断当前所有连接，确定继续吗？"
    },
    {
        "id": "restart_app",
        "name": "重启应用",
        "description": "重启后端应用并清除缓存",
        "icon": "restart",
        "command": "sudo systemctl restart nginx",
        "category": "服务管理",
        "confirm": True,
        "confirm_message": "重启将短暂中断服务，确定继续吗？"
    },
    {
        "id": "view_logs",
        "name": "查看日志",
        "description": "查看应用最近 100 行日志",
        "icon": "log",
        "command": "tail -n 100 /var/log/nginx/access.log",
        "category": "日志监控",
        "confirm": False
    },
    {
        "id": "view_error_logs",
        "name": "错误日志",
        "description": "查看最近 50 行错误日志",
        "icon": "log",
        "command": "tail -n 50 /var/log/nginx/error.log",
        "category": "日志监控",
        "confirm": False
    },
    {
        "id": "check_status",
        "name": "服务状态",
        "description": "查看所有服务的运行状态",
        "icon": "status",
        "command": "systemctl status nginx --no-pager",
        "category": "状态查询",
        "confirm": False
    },
    {
        "id": "disk_usage",
        "name": "磁盘用量",
        "description": "查看服务器磁盘空间使用情况",
        "icon": "status",
        "command": "df -h",
        "category": "状态查询",
        "confirm": False
    },
    {
        "id": "system_info",
        "name": "系统信息",
        "description": "查看服务器基本系统信息",
        "icon": "status",
        "command": "uname -a && uptime && free -h",
        "category": "状态查询",
        "confirm": False
    },
]
