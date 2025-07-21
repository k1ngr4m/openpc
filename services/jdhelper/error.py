class NetworkError(Exception):
    """当网络出现异常波动引发异常时抛出的异常"""

    def __init__(self, message="网络异常波动", details=None):
        self.message = message
        self.details = details

    def __str__(self):
        return (
            f"网络异常波动，请检查网络/代理设置!"
            f"\nmessage: {self.message}" if self.message else ""
                                                              f"\ndetails: {self.details}" if self.details else ""
        )

class TuringVerificationRequiredError(Exception):
    """当自动化流程需要图灵验证时抛出的异常"""

    def __init__(self, message="触发人机验证！", verification_type="", details=None):
        """
        初始化手动验证错误

        Args:
            message: 错误信息
            verification_type: 验证类型
            details: 额外的详细信息
        """
        self.message = message
        self.verification_type = verification_type
        self.details = details
        super().__init__(self.message)

    def __str__(self):
        return (
            f"触发人机验证！"
            f"\nmessage: {self.message}" if self.message else ""
                                                              f"\nverification_type: {self.verification_type}" if self.verification_type else ""
                                                                                                                                              f"\ndetails: {self.details}" if self.details else ""
        )

