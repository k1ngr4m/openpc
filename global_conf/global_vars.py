import os
import threading
from dataclasses import dataclass
from typing import Optional, Any, Callable

from conf import appConf

ENV_KEY_MODE = "APP_MODE"
ZAP_LOGGER_CLEANUP_KEY = "zap_logger"
LOG_WRITER_CLEANUP_KEY = "log_writer"
OTEL_CLEANUP_KEY = "otel"

@dataclass
class AppInfo:
    version: str = ""
    commit: str = ""
    build_time: str = ""
    build_user: str = ""

DEFAULT_APP_CONF : appConf.AppConf = appConf.AppConf()
Conf: appConf.AppConf = appConf.AppConf()
Logger: Optional[Any] = None
cleanups_mu : threading.Lock = threading.Lock()
Cleanups: dict = {}

def is_env_mode_dev() -> bool:
    """环境变量中是否为开发模式"""
    return get_env_mode() == appConf.Mode.DEBUG

def get_env_mode() -> str:
    """获取环境变量中的模式设置"""
    return os.environ.get(ENV_KEY_MODE, "")

def is_dev_mode() -> bool:
    """是否为开发模式"""
    return get_env() == appConf.Mode.DEBUG

def get_env() -> str:
    """获取当前环境模式"""
    return Conf.mode

def is_prod_mode() -> bool:
    """是否为生产模式"""
    return not is_dev_mode()

def set_cleanup(name: str, fn: Callable) -> None:
    """设置清理函数"""
    with cleanups_mu:
        global Cleanups
        Cleanups[name] = fn

def cleanup() -> None:
    """清理资源"""
    import contextlib

    for name, cleanup_func in Cleanups.items():
        if name == LOG_WRITER_CLEANUP_KEY:
            continue
        with contextlib.suppress(Exception):
            cleanup_func()

    if LOG_WRITER_CLEANUP_KEY in Cleanups:
        with contextlib.suppress(Exception):
            Cleanups[LOG_WRITER_CLEANUP_KEY]()