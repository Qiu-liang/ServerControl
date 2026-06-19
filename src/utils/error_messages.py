"""
异常 → 中文友好消息映射
========================
将底层抛出的技术异常转换为用户可理解的中文提示。
"""
import socket
import logging

logger = logging.getLogger(__name__)

# 异常类名（字符串）→ 中文模板映射
# 模板中可使用 {detail} 占位符，由 format_error() 填充
ERROR_MAP = {
    "AuthenticationException":  "服务器密码错误或密钥验证失败，请检查登录凭据。",
    "BadAuthenticationType":    "服务器不支持当前的认证方式，请确认是否使用了正确的登录方法。",
    "SSHException":             "SSH 连接异常：{detail}",
    "socket.timeout":           "连接超时，请检查服务器 IP 和端口是否正确，以及防火墙设置。",
    "TimeoutError":             "操作超时，请检查网络连接或稍后重试。",
    "ConnectionRefusedError":   "连接被拒绝，服务器可能未开启 SSH 服务或端口不正确。",
    "NoValidConnectionsError":  "无法建立连接，请检查网络是否正常以及服务器地址是否正确。",
    "EOFError":                 "服务器主动断开了连接。",
    "PermissionError":          "权限不足：{detail}",
    "FileNotFoundError":        "指定的密钥文件不存在，请检查文件路径。",
    "OSError":                  "系统网络错误：{detail}",
    "ConnectionResetError":     "连接被服务器重置，请检查服务器状态。",
    "IOError":                  "输入输出错误：{detail}",
}


def format_error(exc: Exception) -> str:
    """
    将异常对象转换为用户友好的中文消息。

    参数:
        exc: 捕获到的异常对象

    返回:
        中文错误描述字符串
    """
    exc_type_name = type(exc).__name__
    detail = str(exc) or "未知错误"

    # 1. 精确匹配异常类名
    template = ERROR_MAP.get(exc_type_name)
    if template:
        return template.format(detail=detail)

    # 2. 检查是否为 socket.timeout（特殊处理，因为它是 socket 模块的子类）
    if isinstance(exc, socket.timeout):
        return ERROR_MAP["socket.timeout"]

    # 3. 遍历 MRO，尝试匹配父类
    for cls in type(exc).__mro__:
        cls_name = cls.__name__
        if cls_name in ERROR_MAP:
            return ERROR_MAP[cls_name].format(detail=detail)

    # 4. 兜底
    logger.warning("未找到异常 %s 的中文映射，使用默认消息", exc_type_name)
    return f"操作失败：{detail}"
