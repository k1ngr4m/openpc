import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from conf.appConf import Mode
from global_conf import global_vars
from services.buffApi import update

DEFAULT_TZ = "Asia/Shanghai"
ENV_FILE = ".env"
ENV_LOCAL_FILE = ".env.local"
LOCAL_CONF_FILE = "./config.json"

def init_app() -> Optional[Exception]:
    try:
        # 初始化配置
        init_conf()
        cfg = global_vars.Conf

        # 初始化日志
        init_log(cfg.app_name)

        # 初始化库
        init_lib()

        # 初始化API
        # init_api(global_vars.Conf.buff_api)

        return None
    except Exception as e:
        return e


def init_conf():
    """初始化配置"""
    # 加载环境变量
    load_dotenv(ENV_FILE)
    if os.path.exists(ENV_LOCAL_FILE):
        load_dotenv(ENV_LOCAL_FILE, override=True)

    global_vars.Conf = global_vars.DEFAULT_APP_CONF

    # 设置环境模式
    env_mode = global_vars.is_env_mode_dev()
    if env_mode:
        global_vars.Conf.mode = Mode.DEBUG


def init_log(app_name: str):
    """
    初始化日志

    Args:
        app_name: 应用名称
    """
    # 获取日志级别
    log_level = logging.DEBUG if global_vars.is_dev_mode() else logging.INFO

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 创建日志处理器
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # 设置日志记录器
    global_vars.Logger = logging.getLogger(app_name)
    global_vars.Logger.setLevel(log_level)
    global_vars.Logger.addHandler(handler)

    # 如果是生产模式，添加文件处理器
    if global_vars.is_prod_mode():
        # 获取日志文件路径
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{app_name}.log")

        # 创建文件处理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        global_vars.Logger.addHandler(file_handler)

        # 设置清理函数
        def cleanup_log():
            for handler in global_vars.Logger.handlers:
                handler.close()
                global_vars.Logger.removeHandler(handler)

        global_vars.set_cleanup(global_vars.LOG_WRITER_CLEANUP_KEY, cleanup_log)

def init_lib():
    """
    初始化库
    """
    # 设置时区
    os.environ["TZ"] = DEFAULT_TZ

    return None

def init_api(buff_api_cfg):
    """
    初始化API

    Args:
        buff_api_cfg: API配置
    """
    update.init(buff_api_cfg.url, buff_api_cfg.Timeout)