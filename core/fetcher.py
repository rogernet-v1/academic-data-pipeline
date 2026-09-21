# core/fetcher.py
import asyncio
import time
import random
import httpx
from config.settings import USER_AGENTS, DEFAULT_TIMEOUT
from config.logging_config import logger
from utils.js_runner import JSSignatureRunner


class AsyncFetcher:
    """高并发异步HTTP请求器"""

    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.js_runner = JSSignatureRunner()

    async def fetch(self, client: httpx.AsyncClient, url: str, params: dict = None, retries: int = 3) -> dict:
        async with self.semaphore:
            params = params or {}

            # 追加动态时间戳与 JS 签名参数（对应简历签名处理亮点）
            timestamp = int(time.time())
            sign = self.js_runner.get_signature(url, timestamp)
            params.update({"_t": timestamp, "_sign": sign})

            headers = {"User-Agent": random.choice(USER_AGENTS)}

            for attempt in range(1, retries + 1):
                try:
                    response = await client.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)

                    # 检查 HTTP 状态码
                    if response.status_code == 200:
                        data = response.json()
                        # 检查业务状态码（对应简历“不只判断200”对账点）
                        if data.get("code", 0) == 0:
                            return data
                        else:
                            logger.warning(
                                f"[业务异常] URL: {url} | Code: {data.get('code')} | Message: {data.get('msg')}")

                    logger.warning(f"[HTTP {response.status_code}] 第 {attempt} 次重试 URL: {url}")
                except Exception as e:
                    logger.error(f"[请求异常] 第 {attempt} 次重试 URL: {url} | 错误信息: {e}")

                await asyncio.sleep(1 * attempt)  # 指数退避重试

            return {}