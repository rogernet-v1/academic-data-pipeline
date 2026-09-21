# main.py
import asyncio
import httpx
from config.logging_config import logger
from core.fetcher import AsyncFetcher

async def main():
    logger.info("=== 启动学术文献与开放数据集自动化采集管道 ===")
    
    # 模拟数据源 API (使用 jsonplaceholder 模拟开放数据接口)
    target_urls = [
        f"https://jsonplaceholder.typicode.com/posts/{i}" for i in range(1, 11)
    ]
    
    fetcher = AsyncFetcher(max_concurrent=5)
    
    async with httpx.AsyncClient() as client:
        tasks = [fetcher.fetch(client, url) for url in target_urls]
        results = await asyncio.gather(*tasks)
    
    # 统计数据对账结果（对应简历的数据完整性校验与对账）
    valid_results = [r for r in results if r]
    logger.info(f"=== 采集完成！预期任务数: {len(target_urls)} | 实际有效响应数: {len(valid_results)} ===")

if __name__ == "__main__":
    asyncio.run(main())