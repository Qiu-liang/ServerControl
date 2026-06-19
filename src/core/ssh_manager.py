"""
SSH 管理器
==========
封装 paramiko SSHClient，提供连接、断开、执行命令的接口。
所有方法均为同步阻塞调用，应在线程中使用。
"""
import logging
import time
from typing import Optional, Tuple

import paramiko

logger = logging.getLogger(__name__)


class SSHManager:
    """
    SSH 连接管理器。

    使用方式:
        mgr = SSHManager()
        mgr.connect("192.168.1.1", 22, "root", password="xxx")
        stdout, stderr, exit_code = mgr.exec_command("ls -la")
        mgr.disconnect()
    """

    def __init__(self):
        self._client: Optional[paramiko.SSHClient] = None
        self._connected: bool = False
        self._host: str = ""
        self._port: int = 22
        self._username: str = ""

    @property
    def is_connected(self) -> bool:
        """返回当前是否已连接。"""
        return self._connected and self._client is not None

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def username(self) -> str:
        return self._username

    @property
    def client(self) -> Optional[paramiko.SSHClient]:
        """返回底层 paramiko SSHClient（用于 SFTP 等高级操作）。"""
        return self._client

    def connect(
        self,
        host: str,
        port: int = 22,
        username: str = "root",
        password: Optional[str] = None,
        key_file: Optional[str] = None,
        timeout: int = 15,
    ) -> None:
        """
        建立 SSH 连接。

        参数:
            host: 服务器 IP 或域名
            port: SSH 端口，默认 22
            username: 登录用户名
            password: 密码（与 key_file 二选一）
            key_file: 私钥文件路径（与 password 二选一）
            timeout: 连接超时（秒）

        异常:
            paramiko 相关异常，由调用方捕获并转换为用户消息
        """
        # 先断开已有连接
        if self.is_connected:
            self.disconnect()

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": host,
            "port": port,
            "username": username,
            "timeout": timeout,
            "allow_agent": False,       # 不使用 SSH agent
            "look_for_keys": False,     # 不自动搜索密钥文件
        }

        if key_file:
            connect_kwargs["key_filename"] = key_file
            logger.info("使用私钥连接: %s@%s:%d (key=%s)", username, host, port, key_file)
        else:
            connect_kwargs["password"] = password
            logger.info("使用密码连接: %s@%s:%d", username, host, port)

        client.connect(**connect_kwargs)

        self._client = client
        self._connected = True
        self._host = host
        self._port = port
        self._username = username
        logger.info("SSH 连接成功: %s@%s:%d", username, host, port)

    def disconnect(self) -> None:
        """安全断开 SSH 连接。"""
        if self._client is not None:
            try:
                self._client.close()
                logger.info("SSH 连接已断开: %s@%s:%d", self._username, self._host, self._port)
            except Exception as e:
                logger.warning("断开 SSH 连接时出错: %s", e)
            finally:
                self._client = None
                self._connected = False

    def exec_command(self, command: str, timeout: int = 300) -> Tuple[str, str, int]:
        """
        执行远程命令（阻塞等待完成）。

        参数:
            command: 要执行的 shell 命令
            timeout: 命令超时时间（秒），默认 5 分钟

        返回:
            (stdout 文本, stderr 文本, 退出码)
        """
        if not self.is_connected:
            raise ConnectionError("SSH 未连接，请先建立连接。")

        logger.info("执行命令: %s", command)
        stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)

        stdout_text = stdout.read().decode("utf-8", errors="replace")
        stderr_text = stderr.read().decode("utf-8", errors="replace")
        exit_code = stdout.channel.recv_exit_status()

        logger.info("命令完成，退出码: %d", exit_code)
        return stdout_text, stderr_text, exit_code

    def exec_command_streaming(self, command: str, timeout: int = 300):
        """
        执行远程命令并返回 channel 对象，用于流式读取。

        参数:
            command: 要执行的 shell 命令
            timeout: 命令超时时间（秒）

        返回:
            (stdin, stdout_channel, stderr_channel)
            stdout_channel 和 stderr_channel 支持 readline() 方法
        """
        if not self.is_connected:
            raise ConnectionError("SSH 未连接，请先建立连接。")

        logger.info("流式执行命令: %s", command)
        # 设置 TERM 环境变量，确保 screen 等程序在非交互式 SSH 中能正常运行
        # 用 bash -l 加载 login shell 环境，确保 ~/.bashrc / ~/.profile 被执行
        wrapped = f'bash -l -c {__import__("shlex").quote(command)}'
        stdin, stdout, stderr = self._client.exec_command(
            wrapped,
            timeout=timeout,
            environment={"TERM": "xterm"}
        )
        return stdin, stdout, stderr

    def test_connection(self, host: str, port: int = 22, username: str = "root",
                        password: Optional[str] = None,
                        key_file: Optional[str] = None,
                        timeout: int = 10) -> bool:
        """
        测试 SSH 连接是否可行（连接后立即断开）。

        返回:
            True 表示连接成功，False 表示失败（异常由调用方处理）
        """
        try:
            self.connect(host, port, username, password, key_file, timeout)
            self.disconnect()
            return True
        except Exception:
            self.disconnect()
            raise

    def get_latency_ms(self) -> int:
        """
        测量当前连接的延迟（毫秒）。
        通过执行 echo 命令测量往返时间。
        """
        if not self.is_connected:
            return -1

        start = time.time()
        try:
            self.exec_command("echo ping", timeout=10)
            elapsed = (time.time() - start) * 1000
            return int(elapsed)
        except Exception:
            return -1
