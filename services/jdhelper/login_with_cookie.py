import os
import sys
import time
import json
from typing import Optional

from playwright.async_api import async_playwright, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from services.jdhelper import COOKIES_DIR
from services.jdhelper.error import NetworkError
from services.jdhelper.logger import get_logger
from common.utils import sync_retry

LOG = get_logger()
LOGIN_URL = 'https://passport.jd.com/new/login.aspx'  # 京东登录页面
COOKIES_SAVE_PATH = os.path.join(COOKIES_DIR, "cookies.json")  # 保存 cookies 的路径

@sync_retry(max_retries=3, retry_delay=2, exceptions=(PlaywrightTimeoutError,))
async def __load_page(page: Page, url: str, timeout: float):
    return await page.goto(url, timeout=timeout)


async def logInWithCookies(target_url: str = "https://www.jd.com/", retry: int = 0, context: Optional[BrowserContext] = None):
    """
    使用 cookies 模拟登录

    Params:
        retry: 重新尝试登录的次数
        context: 每次重新尝试登录通用一个 BrowserContext 对象，减少了其初始化的开支
    Returns:
        登录成功时返回 tuple[Page, BrowserContext], 失败则程序退出。
    """
    # 初始化 playwright
    if retry == 0:
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
                headless=False,
                args=["--disable-blink-features", "--disable-blink-features=AutomationControlled"]
            )

        context = await browser.new_context(
            no_viewport=None  # 不限制视口大小
        )

    # 没有 Cookies 先登录获取
    if not os.path.exists(COOKIES_SAVE_PATH):
        LOG.info("未找到 Cookies 文件，将跳转手动登录！")
        page = await context.new_page()  # 这里的 context 在 retry=0时用的local变量，其余情况均使用递归传递的参数
        try:
            response = await __load_page(page, LOGIN_URL, timeout=10000)  # 打开登录界面
            if response.status != 200:
                LOG.error(f"请求错误，状态码：{response.status}")
            else:
                LOG.info("登录页面已跳转，建议使用手机验证码登录以获得较长有效期的 Cookies")
        except PlaywrightTimeoutError:
            raise NetworkError(message=f"页面加载超时：{LOGIN_URL}")

        # 等待用户手动登录京东
        while True:
            try:
                # 检查页面是否已经跳转到京东主页
                await page.wait_for_url(target_url, timeout=3000)
                LOG.success("手动登录成功！")
                break
            except PlaywrightTimeoutError:
                LOG.info("等待用户完成登录...")
        # 获取 Cookies 并保存到文件
        cookies = await page.context.cookies()
        with open(COOKIES_SAVE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=4)
            LOG.info(f'Cookies 已保存到 {os.getcwd()}/cookies.json')
        # 视觉效果优化，以便使用者查看日志信息并进行下一步操作
        await page.close()
        time.sleep(2)

        # 用 Cookies 登录
    page = await context.new_page()
    try:
        await __load_page(page, target_url, timeout=10000)  # 打开登录页面
    except PlaywrightTimeoutError:
        raise NetworkError(message=f"页面加载超时: {target_url}")

    with open(COOKIES_SAVE_PATH, 'r', encoding='utf-8') as f:
        cookies = json.load(f)  # 读取文件中的 cookies
        await page.context.add_cookies(cookies)  # 加载 cookies 到页面上下文
    await page.reload()  # 刷新页面以应用 cookies
    # 检查是否成功登录
    try:
        await page.wait_for_selector('.nickname', timeout=10000)  # 查找一个登录后特有的元素
        LOG.success('使用已保存的 Cookies 登录')
        return page, context
    except PlaywrightTimeoutError:
        if os.path.isfile(COOKIES_SAVE_PATH):  # 每个账号的 cookies 对应一个文件，需要确保删除的是文件
            os.remove(COOKIES_SAVE_PATH)
            LOG.warning('Cookies 已失效，请重新手动登录！')
            # 视觉效果优化，以便使用者查看日志信息并进行下一步操作
            await page.close()
            time.sleep(2)
        if retry >= 3:  # 防止无限递归，但暂未想到发生异常的情况
            LOG.critical("登录异常")
            sys.exit(1)
        else:
            return await logInWithCookies(retry=retry + 1, context=context)  # 尾递归，语义明了
