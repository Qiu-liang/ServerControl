"""
日志配置
========
将日志写入文件，不向控制台输出任何内容。
"""
import logging
import sys

from utils.config_paths import get_log_path

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_initialized = False


def setup_logger(level: int = logging.INFO) -> None:
    """
    配置根日志记录器：只写入文件，不输出到 stderr/stdout。
    幂等设计，多次调用只初始化一次。
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    log_path = get_log_path()
    root = logging.getLogger()
    root.setLevel(level)

    # 文件处理器
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(fh)

    # 禁止向上传播到默认的 stderr handler
    root.propagate = False

    # 移除任何已存在的 stderr handler（防止第三方库打印到控制台）
    for handler in root.handlers[:]:
        if isinstance(handler, logging.StreamHandler) and handler.stream in (sys.stderr, sys.stdout):
            root.removeHandler(handler)

    logging.info("日志系统已初始化，写入: %s", log_path)
