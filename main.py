import asyncio
import logging
import sys
from core.pipeline import DataPipeline
from utils.redis_client import RedisDeduplicator
from spiders.arxiv_spider import ArxivSpider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("academic_pipeline.main")

async def run_pipeline():
    logger.info("=== 启动学术数据异步采集与分析管道 ===")

    # 1. 初始化核心组件
    db_pipeline = DataPipeline()
    dedup = RedisDeduplicator()
    spider = ArxivSpider()

    # 初始化数据库与 Redis
    await db_pipeline.init_db()
    await dedup.connect()

    # 2. 从真实数据源抓取学术数据
    raw_papers = await spider.fetch_papers(search_query="cat:cs.AI", max_results=5)
    
    task_name = "arxiv_cs_ai"
    to_process = []

    # 3. 增量去重校验
    logger.info("开始进行数据增量去重校验...")
    for paper in raw_papers:
        p_id = paper["id"]
        if await dedup.is_duplicate(task_name, p_id):
            logger.info(f"[过滤] 论文 {p_id} 已在 Redis 中存在，自动跳过。")
        else:
            logger.info(f"[放行] 论文 {p_id} 为增量数据，准备写入。")
            to_process.append(paper)

    # 4. 幂等落库与状态回写
    if to_process:
        logger.info(f"正在批量写入 {len(to_process)} 条新增记录至数据库...")
        for paper in to_process:
            success = await db_pipeline.process_item(paper)
            if success:
                await dedup.add_item(task_name, paper["id"])
        logger.info("批量写入完成。")
    else:
        logger.info("本次运行无新增增量数据。")

    # 5. 安全释放资源
    await dedup.close()
    await db_pipeline.close()
    logger.info("=== 学术数据管道任务执行完毕，所有资源已安全释放 ===")

if __name__ == "__main__":
    try:
        asyncio.run(run_pipeline())
    except KeyboardInterrupt:
        logger.info("收到中断指令，任务平滑终止。")