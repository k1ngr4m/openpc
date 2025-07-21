import sys
from global_conf import global_vars
from jdUtil import new_jdUtil
from services.init import init_app


def main():
	# 初始化应用
	err = init_app()
	if err:
		print(f"初始化应用失败:{err}")
		sys.exit(1)

	# 注册清理函数
	import atexit
	atexit.register(global_vars.cleanup)


	# 创建并运行Prophet
	jdutil = new_jdUtil()
	err = jdutil.run()

	if err:
		print(f"运行失败:{err}")
		sys.exit(1)

if __name__ == '__main__':
	main()
