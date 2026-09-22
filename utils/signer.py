import logging
import hashlib
import time
import pyexecjs

logger = logging.getLogger(__name__)

# 模拟前端打包的逆向签名逻辑脚本（JS 代码）
JS_SIGN_SCRIPT = """
function generateToken(params, timestamp) {
    var raw = "academic_v1_" + params + "_" + timestamp + "_secret_salt";
    // 模拟前端混淆的哈希计算
    var hash = 0;
    for (var i = 0; i < raw.length; i++) {
        var char = raw.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash |= 0;
    }
    return "sign_" + Math.abs(hash).toString(16);
}
"""

class RequestSigner:
    """
    Web 逆向工程工具类
    负责破解/执行前端签名逻辑，为高阶爬虫请求生成鉴权 Token/Sign
    """
    def __init__(self):
        try:
            self.ctx = pyexecjs.compile(JS_SIGN_SCRIPT)
            logger.info("PyExecJS 逆向签名环境初始化成功。")
        except Exception as e:
            logger.warning(f"PyExecJS 初始化失败，启用 Python 纯算法降级方案: {e}")
            self.ctx = None

    def sign_request(self, param_str: str) -> dict:
        """
        生成带有时间戳和加密签名的请求头参数
        """
        timestamp = int(time.time())
        if self.ctx:
            try:
                token = self.ctx.call("generateToken", param_str, timestamp)
            except Exception as e:
                logger.error(f"JS 执行签名失败: {e}")
                token = self._python_fallback_sign(param_str, timestamp)
        else:
            token = self._python_fallback_sign(param_str, timestamp)

        return {
            "X-Sign-Token": token,
            "X-Timestamp": str(timestamp),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _python_fallback_sign(self, param_str: str, timestamp: int) -> str:
        raw = f"academic_v1_{param_str}_{timestamp}_secret_salt"
        return "sign_" + hashlib.md5(raw.encode('utf-8')).hexdigest()[:12]