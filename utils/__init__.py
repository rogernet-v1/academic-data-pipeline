class RequestSigner:
    """
    Web 逆向工程工具类
    负责破解/执行前端签名逻辑，为高阶爬虫请求生成鉴权 Token/Sign
    """
    def __init__(self):
        try:
            self.ctx = execjs.compile(JS_SIGN_SCRIPT)
            logger.info("PyExecJS 逆向签名环境初始化成功。")
        except Exception as e:
            logger.warning(f"PyExecJS 初始化失败，启用 Python 纯算法降级方案: {e}")
            self.ctx = None