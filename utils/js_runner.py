# utils/js_runner.py
import execjs
from config.logging_config import logger


class JSSignatureRunner:
    """前端混淆签名逆向调用工具"""

    def __init__(self):
        # 模拟前端生成的加密/签名算法逻辑
        self.js_code = """
        function generateSignature(params, timestamp) {
            // 模拟混淆签名逻辑：将参数与时间戳进行简单哈希计算
            var rawStr = params + "_" + timestamp + "_secret_key_2026";
            var hash = 0;
            for (var i = 0; i < rawStr.length; i++) {
                hash = (hash << 5) - hash + rawStr.charCodeAt(i);
                hash |= 0;
            }
            return "sign_" + Math.abs(hash);
        }
        """
        try:
            self.ctx = execjs.compile(self.js_code)
        except Exception as e:
            logger.error(f"ExecJS 编译签名代码失败: {e}")
            self.ctx = None

    def get_signature(self, params: str, timestamp: int) -> str:
        """调用 JS 签名函数"""
        if not self.ctx:
            return ""
        try:
            sign = self.ctx.call("generateSignature", params, timestamp)
            return sign
        except Exception as e:
            logger.error(f"执行 JS 动态签名异常: {e}")
            return ""