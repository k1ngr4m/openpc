import asyncio
import re
import signal
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from typing import Optional, Any, Callable

from fastapi import FastAPI
from flask import Request

from common.utils import sync_retry
from global_conf import global_vars
from option import ApplyOption, WithDebug, WithProd
from api import Api
from routes import register_routes
from services.db.remote.mysqlutil import MysqlUtil
import services.logger.logger as logger
import uvicorn
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Locator, ElementHandle, Page

from services.jdhelper.error import NetworkError
from services.jdhelper.login_with_cookie import logInWithCookies as async_logInWithCookies


class CancellationContext:
    def __init__(self):
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled

class Options:
    def __init__(self,
                 debug: bool = False,
                 enable_pprof: bool = True,
                 http_addr: str = "127.0.0.1:8090"):
        self.debug = debug
        self.enable_pprof = enable_pprof
        self.http_addr = http_addr

default_opts = Options()

class jdUtil:
    def __init__(self,
                 ctx: Optional[Any] = None,
                 opts: Optional[Options] = None,
                 http_srv: Optional[Any] = None,
                 pw_active: bool = False,
                 cancel: Optional[Callable[[], None]] = None,
                 api: Optional[Api] = None,
                 lock: Optional[threading.Lock] = None,
                 mysql: Optional[Any] = None):
        self._event_loop = None  # 存储事件循环引用
        self.ctx = ctx
        self.opts = opts if opts is not None else default_opts
        self.http_srv = http_srv
        self.pw_active = pw_active
        self.lcu_client = None
        self.cancel = cancel
        self.api = api
        self.lock = lock if lock is not None else threading.Lock()
        self.mysql = mysql

        self.__page, browser = None, None
        self.__err_occurred = False

    async def init_page(self):
        self.__page, _ = await async_logInWithCookies()

    def init_api(self):
        # 确保 api 已初始化
        if self.api is None:
            raise RuntimeError("Api instance is not initialized")

        # 1. 根据 debug 标志创建 FastAPI 应用
        debug = bool(self.opts.debug)
        app = FastAPI(debug=debug)


        @app.middleware("http")
        async def recovery_and_log(request: Request, call_next):
            try:
                response = await call_next(request)
                return response
            except Exception as exc:
                logger.error("Unhandled exception in request:", exc_info=exc)
                from fastapi.responses import PlainTextResponse
                return PlainTextResponse("Internal Server Error", status_code=500)

        # 5. 注册路由
        register_routes(app, self.api)

        # 6. 创建并保存 Uvicorn 服务器实例（未运行）
        host_str, port_str = self.opts.http_addr.split(":")
        host = host_str.strip()
        port = int(port_str.strip())

        uvicorn_config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="debug" if debug else "info",
        )
        server = uvicorn.Server(uvicorn_config)

        # 7. 将 app 与 server 保存在实例属性中
        self.app = app
        self.http_srv = server

    def init_web_view(self):
        """
        初始化 WebView 界面（在浏览器中打开应用界面）
        """
        try:
            # 获取基础 URL
            website_url = global_vars.Conf.web_view.IndexUrl
            logger.info(f"请手动访问: {website_url}")

        except Exception as e:
            logger.error(f"初始化 WebView 时出错: {e}")

    async def run_async(self):
        # 初始化 Web 接口服务
        self.init_api()
        
        # 初始化 WebView（界面服务）routes.py
        threading.Thread(target=self.init_web_view, daemon=True).start()
        
        # 保存事件循环引用
        self._event_loop = asyncio.get_running_loop()
        
        # 初始化页面
        await self.init_page()
        time.sleep(3)
        await self.__page.close()
        logger.info(
            f"{global_vars.Conf.app_name} 已启动 -- {global_vars.Conf.website_title}"
        )
        
        # 运行主循环
        await self.notify_quit()
        
    def run(self):
        asyncio.run(self.run_async())


    async def notify_quit(self):
        """
        等待程序退出信号，管理服务器生命周期
        """
        # 创建事件循环
        loop = asyncio.get_running_loop()
        interrupt_event = asyncio.Event()

        # # 设置中断信号处理
        # interrupt_event = asyncio.Event()
        # for sig in (signal.SIGINT, signal.SIGTERM):
        #     loop.add_signal_handler(sig, interrupt_event.set)

        # Windows 专用信号处理
        def signal_handler(sig, frame):
            logger.info("收到 Ctrl+C 信号")
            interrupt_event.set()

        signal.signal(signal.SIGINT, signal_handler)

        # 创建线程池用于运行阻塞操作
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 任务1: 运行HTTP服务器
            server_task = loop.run_in_executor(
                executor,
                self.http_srv.run
            )

            # 任务2: 监听中断信号
            async def watch_interrupt():
                await interrupt_event.wait()
                logger.info("收到退出信号，正在关闭服务器...")

                # 调用停止方法
                await self.stop()

                # 关闭服务器
                with suppress(Exception):
                    await self.http_srv.shutdown()

            interrupt_task = asyncio.create_task(watch_interrupt())

            # 任务3: 监听上下文取消
            async def watch_context():
                while not self.ctx.cancelled:
                    await asyncio.sleep(0.1)
                logger.info("上下文已取消，正在关闭服务器...")
                interrupt_event.set()

            context_task = asyncio.create_task(watch_context())

            # 等待所有任务完成
            done, pending = await asyncio.wait(
                [server_task, interrupt_task, context_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # 取消未完成的任务
            for task in pending:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

            # 检查是否有错误
            for task in done:
                if task.exception():
                    logger.error(f"任务异常: {task.exception()}")
                    return task.exception()

        return None

    async def stop(self):
        """停止服务，清理资源"""
        logger.info("正在停止服务...")

        # 清理其他资源
        # ...

        # 标记上下文为已取消
        self.ctx.cancel()
        logger.info("服务已停止")


    async def query_sku_info(self, sku_code):
        '''
        获取商品对应的价格
        :return:
            {
                'sku_code': sku_code,
                'sku_name': sku_name,
                'price': price_value
            }
        '''
        # if not self.__page or self.__page.is_closed():
        #     await self.init_page()
            
        url_1 = f'https://item.jd.com/{sku_code}.html'
        sku_name = ''
        price_value = 0.00
        brand_name = ''
        is_taken_down = 0
        try:
            await self.__load_page(url_1, timeout=20000)
        except PlaywrightTimeoutError:
            raise NetworkError(message=f"页面加载超时：{url_1}")
            
        try:
            await self.__page.wait_for_selector('.sku-name-title', timeout=5000)
            sku_name_element = self.__page.locator('.sku-name-title')
            sku_name = await sku_name_element.inner_text()
            logger.info(f'商品名称: {sku_name}')
        except Exception as e:
            logger.error(f"获取商品名称失败: {e}")

        try:
            await self.__page.wait_for_selector('.summary-price.J-summary-price .p-price .price', timeout=5000)
            price_element = self.__page.locator('.summary-price.J-summary-price .p-price .price')
            price_text = await price_element.inner_text()
            price_value = float(price_text.split('¥')[-1].strip())
            logger.info(f'商品价格: {price_value}')
        except Exception as e:
            logger.error(f"获取商品价格失败: {e}，可能已经下架了")
            is_taken_down = 1
        finally:
            time.sleep(2)
            await self.__page.close()

        if sku_name:
            brand_name = self.extract_brand(sku_name)
        return {
            'sku_code': sku_code,
            'sku_name': sku_name,
            'price': price_value,
            'url': url_1,
            'brand': brand_name,
            'is_taken_down': is_taken_down
        }

    @sync_retry(max_retries=3, retry_delay=2, exceptions=(PlaywrightTimeoutError,))
    async def __load_page(self, url: str, timeout: float):
        # if not self.__page or self.__page.is_closed():
        #     await self.init_page()
        # 确保在正确的事件循环中执行
        if self._event_loop and self._event_loop != asyncio.get_running_loop():
            # 在正确循环中重新初始化页面
            self.__page = None
            await self.init_page()
        return await self.__page.goto(url, timeout=timeout)

    def extract_brand(self, sku_name):
        """
        从商品名称中提取品牌信息
        规则：优先取第一个括号前的内容，若无括号则取第一个空格前的内容
        """
        print(sku_name)
        if not sku_name:
            return ""

        # 模式1：匹配"品牌（英文）"结构（支持中英文括号）
        pattern1 = r'^([^\(\（]+?)\s*[\(\（]'
        # 模式2：匹配首个空格前的连续非空字符
        pattern2 = r'^(\S+?)\s'

        # 先尝试匹配括号模式
        match = re.search(pattern1, sku_name)
        if match:
            return match.group(1).strip()

        # 再尝试匹配空格模式
        match = re.search(pattern2, sku_name)
        if match:
            return match.group(1).strip()

        # 两种模式都不匹配时取前5个字符（防止过长无效字符）
        return sku_name[:5].strip()


def new_jdUtil(*apply_options: ApplyOption) -> jdUtil:
    ctx = CancellationContext()
    cancel = ctx.cancel
    mysql = MysqlUtil()
    # 创建实例
    p = jdUtil(
        ctx=ctx,
        cancel=cancel,
        lock=threading.Lock(),
        opts=default_opts,
        mysql=mysql
    )
    # 设置开发/生产模式
    if global_vars.is_dev_mode():
        apply_options = (*apply_options, WithDebug())
    else:
        apply_options = (*apply_options, WithProd())

    # 应用选项
    for fn in apply_options:
        fn(p.opts)

    # 关键：在返回之前创建并设置 Api 实例
    p.api = Api(p)  # 确保 Api 被正确初始化

    return p