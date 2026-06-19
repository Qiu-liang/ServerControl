"""
加密工具模块
============
使用 Fernet 对称加密 + PBKDF2 密钥派生，安全存储敏感凭据。
密钥从机器唯一标识派生，无需用户记忆额外密码。
"""
import os
import uuid
import hashlib
import base64
import logging

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

logger = logging.getLogger(__name__)

# 固定盐值（结合机器 GUID 使用，保证同一台机器每次派生相同密钥）
_SALT = b"ServerControl-Salt-v1"
_KDF_ITERATIONS = 100_000


def _get_machine_id() -> str:
    """
    获取机器唯一标识符。
    Windows: 使用 MachineGuid 注册表项；
    其他平台: 使用 uuid.getnode()（MAC 地址）。
    """
    if os.name == "nt":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY
            )
            machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            return machine_guid
        except Exception:
            pass

    # 回退：使用 MAC 地址 + 主机名
    return f"{uuid.getnode()}-{os.getenv('COMPUTERNAME', 'unknown')}"


def derive_key() -> bytes:
    """
    从机器标识派生 Fernet 加密密钥（32 字节，base64 编码）。
    同一台机器每次调用返回相同的密钥。

    返回:
        适用于 Fernet 的 base64 编码密钥
    """
    machine_id = _get_machine_id()
    password = machine_id.encode("utf-8")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=_KDF_ITERATIONS,
    )
    raw_key = kdf.derive(password)
    # Fernet 要求 base64 编码的 32 字节密钥
    return base64.urlsafe_b64encode(raw_key)


def encrypt_data(plaintext: str) -> bytes:
    """
    使用 Fernet 加密字符串。

    参数:
        plaintext: 要加密的明文字符串

    返回:
        Fernet token（bytes）
    """
    key = derive_key()
    f = Fernet(key)
    return f.encrypt(plaintext.encode("utf-8"))


def decrypt_data(token: bytes) -> str:
    """
    使用 Fernet 解密 token。

    参数:
        token: Fernet 加密的 token（bytes）

    返回:
        解密后的明文字符串

    异常:
        cryptography.fernet.InvalidToken: 密钥不匹配或 token 被篡改
    """
    key = derive_key()
    f = Fernet(key)
    return f.decrypt(token).decode("utf-8")
