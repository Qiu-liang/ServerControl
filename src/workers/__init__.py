"""
后台任务执行器
==============
使用标准 threading 模块在后台线程执行网络操作。
通过 tkinter 的 after() 方法将结果安全地回调到主线程。

替代 PyQt6 的 QThread + Worker 模式。
"""
import threading
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class TaskRunner:
    """
    后台任务执行器。

    使用方式:
        runner = TaskRunner(root)
        runner.run(
            task=lambda: ssh_manager.connect(...),
            on_success=lambda result: print("connected"),
            on_error=lambda msg: print(f"error: {msg}")
        )
    """

    def __init__(self, root):
        """
        参数:
            root: tkinter 根窗口，用于 after() 回调
        """
        self._root = root

    def run(self, task: Callable, on_success: Callable = None,
            on_error: Callable = None, on_start: Callable = None):
        """
        在后台线程中执行任务。

        参数:
            task: 要执行的函数（在工作线程中运行）
            on_success: 成功回调，接收 task 的返回值（主线程）
            on_error: 错误回调，接收中文错误消息字符串（主线程）
            on_start: 开始前回调（主线程）
        """
        if on_start:
            on_start()

        def _worker():
            try:
                result = task()
                if on_success:
                    self._root.after(0, lambda: on_success(result))
            except Exception as e:
                from utils.error_messages import format_error
                msg = format_error(e)
                logger.error("后台任务失败: %s", msg)
                if on_error:
                    self._root.after(0, lambda: on_error(msg))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t


class StreamTaskRunner:
    """
    支持流式输出的后台任务执行器（用于命令执行）。

    使用方式:
        runner = StreamTaskRunner(root)
        runner.run_command(
            ssh_manager=ssh_mgr,
            command="ls -la",
            on_output=lambda line, is_err: console.append(line, is_err),
            on_finished=lambda code: console.append_footer(code),
            on_error=lambda msg: console.append_error(msg)
        )
    """

    def __init__(self, root):
        self._root = root
        self._cancelled = False
        self._channel = None

    def run_command(self, ssh_manager, command: str,
                    on_output: Callable = None,
                    on_finished: Callable = None,
                    on_error: Callable = None,
                    on_start: Callable = None,
                    timeout: int = 300):
        """
        在后台线程中执行命令，支持流式输出。

        参数:
            ssh_manager: SSHManager 实例
            command: 要执行的命令
            on_output: 每行输出回调 (text, is_error)（主线程）
            on_finished: 完成回调 (exit_code)（主线程）
            on_error: 错误回调 (msg)（主线程）
            on_start: 开始前回调（主线程）
            timeout: 超时秒数
        """
        self._cancelled = False
        if on_start:
            on_start()

        def _worker():
            try:
                stdin, stdout, stderr = ssh_manager.exec_command_streaming(
                    command, timeout=timeout
                )
                self._channel = stdout.channel

                # 逐行读取 stdout
                for line in iter(stdout.readline, ""):
                    if self._cancelled:
                        break
                    text = line.rstrip("\n\r")
                    if text and on_output:
                        self._root.after(0, lambda t=text: on_output(t, False))

                # 逐行读取 stderr
                for line in iter(stderr.readline, ""):
                    if self._cancelled:
                        break
                    text = line.rstrip("\n\r")
                    if text and on_output:
                        self._root.after(0, lambda t=text: on_output(t, True))

                exit_code = stdout.channel.recv_exit_status()
                if on_finished:
                    self._root.after(0, lambda: on_finished(exit_code))

            except Exception as e:
                from utils.error_messages import format_error
                msg = format_error(e)
                if on_error:
                    self._root.after(0, lambda: on_error(msg))
            finally:
                self._channel = None

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t

    def cancel(self):
        """取消正在执行的命令。"""
        self._cancelled = True
        if self._channel:
            try:
                self._channel.close()
            except Exception:
                pass
