"""
凭据存储模块
============
双后端策略：
1. 优先使用 keyring（Windows Credential Manager）—— 安全性最高
2. 回退到 Fernet 加密文件 —— 兼容性兜底

对外暴露统一的 get/set/delete 接口，上层无需关心底层存储方式。
"""
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List

from utils.config_paths import get_encrypted_config_path
from security.crypto_utils import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)

# keyring 服务名（在 Windows 凭据管理器中显示的名称）
_SERVICE_NAME = "ServerControl"

# 运行时缓存：记录 keyring 是否可用
_keyring_available: Optional[bool] = None
_keyring = None


def _try_import_keyring():
    """尝试导入 keyring，缓存结果。"""
    global _keyring_available, _keyring
    if _keyring_available is not None:
        return _keyring_available

    try:
        import keyring as kr
        _keyring = kr
        # 测试 keyring 是否真正可用（某些精简版 Windows 可能没有凭据管理器）
        _keyring.get_password(_SERVICE_NAME, "__keyring_test__")
        _keyring_available = True
        logger.info("keyring 可用，将使用系统凭据管理器")
    except Exception as e:
        _keyring_available = False
        logger.warning("keyring 不可用 (%s)，将回退到加密文件", e)

    return _keyring_available


# ── 加密文件后端 ─────────────────────────────────────────────────────────────

def _load_encrypted_store() -> dict:
    """从加密文件加载凭据存储。"""
    path = get_encrypted_config_path()
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "rb") as f:
            token = f.read()
        if not token:
            return {}
        plaintext = decrypt_data(token)
        return json.loads(plaintext)
    except Exception as e:
        logger.error("解密凭据文件失败: %s", e)
        return {}


def _save_encrypted_store(data: dict) -> None:
    """将凭据存储加密后写入文件。"""
    path = get_encrypted_config_path()
    plaintext = json.dumps(data, ensure_ascii=False)
    token = encrypt_data(plaintext)
    with open(path, "wb") as f:
        f.write(token)
    logger.info("凭据已加密保存到: %s", path)


# ── 统一接口 ─────────────────────────────────────────────────────────────────

class CredentialStore:
    """
    凭据存取管理器。

    使用方式:
        store = CredentialStore()
        store.set_password("my_server", "my_password")
        pwd = store.get_password("my_server")
        store.delete_password("my_server")

    连接配置（多字段）存取:
        store.set_connection("my_server", {"host": "1.2.3.4", "port": 22, ...})
        cfg = store.get_connection("my_server")
    """

    def set_password(self, username: str, password: str) -> None:
        """保存密码。"""
        if _try_import_keyring():
            try:
                _keyring.set_password(_SERVICE_NAME, username, password)
                logger.info("密码已保存到 keyring: %s", username)
                return
            except Exception as e:
                logger.warning("keyring 写入失败，回退到加密文件: %s", e)

        # Fernet 文件回退
        store = _load_encrypted_store()
        store[f"pwd:{username}"] = password
        _save_encrypted_store(store)

    def get_password(self, username: str) -> Optional[str]:
        """读取密码，不存在返回 None。"""
        if _try_import_keyring():
            try:
                val = _keyring.get_password(_SERVICE_NAME, username)
                if val is not None:
                    return val
            except Exception:
                pass

        store = _load_encrypted_store()
        return store.get(f"pwd:{username}")

    def delete_password(self, username: str) -> None:
        """删除密码。"""
        if _try_import_keyring():
            try:
                _keyring.delete_password(_SERVICE_NAME, username)
            except Exception:
                pass

        store = _load_encrypted_store()
        store.pop(f"pwd:{username}", None)
        _save_encrypted_store(store)

    def set_connection(self, name: str, config: dict) -> None:
        """
        保存完整的连接配置（不含密码）。
        密码通过 set_password 单独存储。
        """
        store = _load_encrypted_store()
        store[f"conn:{name}"] = config
        _save_encrypted_store(store)
        logger.info("连接配置已保存: %s", name)

    def get_connection(self, name: str) -> Optional[dict]:
        """读取连接配置，不存在返回 None。"""
        store = _load_encrypted_store()
        return store.get(f"conn:{name}")

    def delete_connection(self, name: str) -> None:
        """删除连接配置。"""
        store = _load_encrypted_store()
        store.pop(f"conn:{name}", None)
        _save_encrypted_store(store)

    def list_connections(self) -> list:
        """返回所有已保存的连接名称列表。"""
        store = _load_encrypted_store()
        return [
            key.replace("conn:", "", 1)
            for key in store.keys()
            if key.startswith("conn:")
        ]

    def set_key_path(self, username: str, key_file_path: str) -> None:
        """保存私钥文件路径（以加密形式存储）。"""
        store = _load_encrypted_store()
        store[f"keypath:{username}"] = key_file_path
        _save_encrypted_store(store)

    def get_key_path(self, username: str) -> Optional[str]:
        """读取私钥文件路径。"""
        store = _load_encrypted_store()
        return store.get(f"keypath:{username}")

    def save_session_history(self, name: str, config: dict, success: bool = True) -> None:
        """
        保存会话历史记录。
        
        参数:
            name: 会话名称
            config: 连接配置字典
            success: 连接是否成功
        """
        store = _load_encrypted_store()
        history_key = f"history:{name}"
        
        # 获取现有历史记录或创建新记录
        history = store.get(history_key, {})
        
        # 更新历史记录
        history["last_connect_time"] = datetime.now().isoformat()
        history["success"] = success
        history["connect_count"] = history.get("connect_count", 0) + 1
        # 保存基本连接信息（不含密码）
        history["host"] = config.get("host", "")
        history["port"] = config.get("port", 22)
        history["username"] = config.get("username", "")
        
        store[history_key] = history
        _save_encrypted_store(store)
        logger.info("会话历史已保存: %s", name)

    def get_session_history(self) -> List[Dict]:
        """
        获取所有会话历史记录。
        
        返回:
            包含会话历史记录的列表，按最后连接时间降序排列
        """
        store = _load_encrypted_store()
        history_list = [] 
        
        for key, value in store.items():
            if key.startswith("history:"):
                name = key.replace("history:", "", 1)
                history_entry = {
                    "name": name,
                    "last_connect_time": value.get("last_connect_time", ""),
                    "success": value.get("success", False),
                    "connect_count": value.get("connect_count", 0),
                    "host": value.get("host", ""),
                    "port": value.get("port", 22),
                    "username": value.get("username", "")
                }
                history_list.append(history_entry)
        
        # 按最后连接时间降序排序
        history_list.sort(key=lambda x: x["last_connect_time"], reverse=True)
        return history_list

    def delete_session_history(self, name: str) -> None:
        """
        删除会话历史记录。
        
        参数:
            name: 会话名称
        """
        store = _load_encrypted_store()
        store.pop(f"history:{name}", None)
        _save_encrypted_store(store)
        logger.info("会话历史已删除: %s", name)
