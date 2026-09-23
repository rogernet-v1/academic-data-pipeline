import asyncio
import logging
import sys
from core.pipeline import DataPipeline
from utils.redis_client import RedisDeduplicator
from spiders.arxiv_spider import ArxivSpider
from spiders.crossref_spider import CrossrefSpider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("academic_pipeline.main")


async def run_pipeline():
    logger.info("=== 启动多数据源学术异步采集管道 ===")

    # 1. 初始化核心组件与爬虫列表
    db_pipeline = DataPipeline()
    dedup = RedisDeduplicator()

    spiders = [
        (ArxivSpider(), "cat:cs.AI"),
        (CrossrefSpider(), "machine learning")
    ]

    await db_pipeline.init_db()
    await dedup.connect()

    # 2. 遍历各数据源执行采集
    for spider, query in spiders:
        logger.info(f"--- 开始数据源 [{spider.source_name}] 抓取，检索词: '{query}' ---")
        papers = await spider.fetch_papers(search_query=query, max_results=3)

        task_name = f"{spider.source_name}_task"
        to_process = []

        # 3. 增量去重校验
        for paper in papers:
            p_id = paper.paper_id
            if await dedup.is_duplicate(task_name, p_id):
                logger.info(f"[过滤] 论文 [{paper.source}] {p_id} 已存在，跳过。")
            else:
                logger.info(f"[放行] 论文 [{paper.source}] {p_id} 新增数据。")
                to_process.append(paper)

        # 4. 统一持久化落库
        if to_process:
            logger.info(f"写入 {len(to_process)} 条 [{spider.source_name}] 记录至数据库...")
            for paper in to_process:
                success = await db_pipeline.process_item(paper)
                if success:
                    await dedup.add_item(task_name, paper.paper_id)
            logger.info(f"[{spider.source_name}] 写入完成。")
        else:
            logger.info(f"[{spider.source_name}] 无新增数据。")

    # 5. 安全释放资源
    await dedup.close()
    await db_pipeline.close()
    logger.info("=== 管道任务执行完毕，资源已安全释放 ===")


if __name__ == "__main__":
    try:
        asyncio.run(run_pipeline())
    except KeyboardInterrupt:
        logger.info("收到中断指令，任务平滑终止。")