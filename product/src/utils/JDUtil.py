import os
import re
import sys
import time
import random
import hashlib
import secrets
import argparse
import requests
from PIL import Image, ImageFilter
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Locator, ElementHandle, Page
from typing import List, Optional

from product.src.utils import sku_code_list
from product.src.data import EvaluationTask, TuringVerificationRequiredError, NetworkError, DEFAULT_COMMENT_TEXT_LIST
from product.src.logger import get_logger, init_logger
from product.src.login_with_cookie import logInWithCookies
from common.utils import *

LOG = get_logger()


class JDUtil(object):
	LOG_LEVEL: str = "INFO"                          # 日志记录等级

	def __init__(self) -> None:
		self.__page, browser = None, None
		self.__task_list: List[EvaluationTask] = []
		self.__start_time = time.time()  # 标记初始化时间戳
		self.__err_occurred = False

	@classmethod
	def parse_args(cls):
		"""解析命令行参数，并直接修改类属性"""
		parser = argparse.ArgumentParser()

		parser.add_argument('-v', '--version', action='version', version='%(prog)s version: 2.9.19')
		# parser.add_argument('-T', '--supported-table', action=ShowSupportedTableAction, help="show supported AI groups and models")
		parser.add_argument('-L', '--log-level', type=str, default="INFO", dest="log_level", help="DEBUG < INFO < WARNING < ERROR < CRITICAL")

		args = parser.parse_args()  # 解析命令行参数

		# 直接使用dest参数的全大写形式更新类属性
		for key, value in vars(args).items():
			if value is not None and hasattr(cls, key.upper()):
				setattr(cls, key.upper(), value)
		return cls

	def init(self):
		"""主循环"""
		try:
			init_logger(self.LOG_LEVEL)
			self.__page, _ = logInWithCookies()
			return True
		except Exception as err:
			self.__err_occurred = True
			LOG.error(f"执行过程中发生异常: {str(err)}")
			if self.LOG_LEVEL == "DEBUG":
				raise # 调试专用

	def get_sku_info(self, sku_code):
		'''
		获取商品对应的价格
		:return:
			{
				'sku_code': sku_code,
				'sku_name': sku_name,
				'price': price_value
			}
		'''
		url_1 = f'https://item.jd.com/{sku_code}.html'
		sku_name = ''
		price_value = 0.00
		try:
			self.__load_page(url_1, timeout=20000)
		except PlaywrightTimeoutError:
			raise NetworkError(message=f"页面加载超时：{url_1}")
		try:
			self.__page.wait_for_selector('.sku-name-title', timeout=5000)
			sku_name_element = self.__page.locator('.sku-name-title')
			sku_name = sku_name_element.inner_text()
			LOG.info(f'商品名称: {sku_name}')
		except Exception as e:
			LOG.error(f"获取商品名称失败: {e}")

		try:
			self.__page.wait_for_selector('.summary-price.J-summary-price .p-price .price')
			price_element = self.__page.locator('.summary-price.J-summary-price .p-price .price')
			price_text = price_element.inner_text()
			price_value = float(price_text.split('¥')[-1].strip())
			LOG.info(f'商品价格: {price_value}')
		except Exception as e:
			LOG.error(f"获取商品价格失败: {e}")
		return {
			'sku_code': sku_code,
			'sku_name': sku_name,
			'price': price_value
		}

	def get_sku_info_list(self):
		sku_info_list = []
		for sku_code in sku_code_list:
			sku_info = self.get_sku_info(sku_code)
			if sku_info:
				sku_info_list.append(sku_info)
		LOG.info(f'商品信息列表: {sku_info_list}')
		return sku_info_list

	def __requires_TuringVerification(self) -> bool:
		"""判断是否进入图灵验证界面"""
		# 该方法是通过 timeout 异常调用的，也就是说在自动化流程中出现了元素获取失败的情况，即使在此刻通过了人机验证，也无法回到上一步（获取元素）
		# 1. 所有等待元素的方法都进行retry 2.跳过当前任务，继续往下进行（不适用于连续多个任务都出现人机验证的情况）
		try:
			# 一般来说，进入测试页面时 page 还在等待其他元素，故 timeout 不宜过大，进而确保整体性能。
			if self.__page.wait_for_selector('.verifyBtn', timeout=1500):
				'''
				match self.DEAL_TURING_VERIFCATION:
					case 0:
						raise TuringVerificationRequiredError(message="当前设置--自动退出")
					case 1:
						self.__handle_TuringVerification()
					case _ as e:
						LOG.error(f"DEAL_TURING_VERIFCATION 参数所选值 {e} 非法！")
				'''
				LOG.error('当前页面需要人机验证')
		except PlaywrightTimeoutError:
			pass
		return False

	def __handle_TuringVerification(self) -> bool:
		"""
		进行图灵测试

		Returns:
			图灵测试是否通过(bool):
		"""
		turing_url = self.__page.url
		LOG.debug(f"{turing_url}")
		LOG.info("等待手动人机验证......")
		while True:
			# 检测是否通过验证：1.是否还在验证页面 2.根据验证页面的 url 参数 returnurl 可以获取测试成功后的跳转页面
			# 但是不同类型的的商品最终重定向的页面 url 与 returnurl 不完全匹配，如京东国际等
			try:
				# 持续检测页面 url，一经变动立刻抛出异常
				self.__page.wait_for_url(turing_url, timeout=0.1) # 为了 url 检测的灵敏度更高，超时时长应设置的尽可能小
				self.__page.wait_for_timeout(timeout=200) # url 保持在测试时页面会快速的循环，考虑到性能方面建议阻塞
			except PlaywrightTimeoutError:
				# 暂认为，离开验证页面即为验证通过
				LOG.success("人机验证已通过")
				return True

	@sync_retry(max_retries=3, retry_delay=2, exceptions=(PlaywrightTimeoutError,))
	def __load_page(self, url: str, timeout: float):
		return self.__page.goto(url, timeout=timeout)

def new_jd():
	jd = JDUtil()
	return jd
