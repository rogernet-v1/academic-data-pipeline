import asyncio
import logging
import sys
from core.pipeline import DatabasePipeline
from utils.redis_client import RedisDeduplicator

# 配置全局日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("academic_pipeline.main")

async def run_pipeline():
    """
    数据管道主运行引擎：初始化 -> 增量去重 -> 数据库批量落库
    """
    logger.info("=== 启动学术数据异步采集与分析管道 ===")

    # 1. 初始化核心组件
    db_pipeline = DatabasePipeline()
    dedup = RedisDeduplicator()

    # 初始化数据库建表结构与 Redis 连接
    await db_pipeline.init_db()
    await dedup.connect()

    # 模拟构建采集批次数据 (学术论文 meta 样例)
    sample_papers = [
        {
            "paper_id": "arxiv_2401.00001",
            "title": "Scalable Asynchronous Pipelines for Large-Scale Academic Data Processing",
            "authors": ["Alice Smith", "Bob Johnson"],
            "abstract": "We present an asynchronous data pipeline model using Python, Redis, and PostgreSQL.",
            "source": "arXiv",
            "publish_year": 2024
        },
        {
            "paper_id": "arxiv_2401.00002",
            "title": "Optimizing Incremental Web Crawling with Redis Bloom Filters",
            "authors": ["Charlie Brown"],
            "abstract": "This study evaluates deduplication latency across Redis datastructures.",
            "source": "arXiv",
            "publish_year": 2024
        }
    ]

    task_name = "arxiv_computer_science"
    to_process = []

    # 2. 管道去重校验阶段
    logger.info("开始进行数据增量去重校验...")
    for paper in sample_papers:
        p_id = paper["paper_id"]
        if await dedup.is_duplicate(task_name, p_id):
            logger.info(f"[过滤] 论文 {p_id} 已在 Redis 中存在，自动跳过。")
        else:
            logger.info(f"[放行] 论文 {p_id} 为增量数据，准备写入。")
            to_process.append(paper)

    # 3. 数据落库与状态回写阶段
    if to_process:
        logger.info(f"正在批量写入 {len(to_process)} 条记录至数据库...")
        success_count = await db_pipeline.upsert_papers(to_process)
        logger.info(f"成功更新/入库 {success_count} 条记录。")

        # 将写库成功的记录标记到 Redis 去重集合
        for paper in to_process:
            await dedup.add_item(task_name, paper["paper_id"])
    else:
        logger.info("本次运行无新增增量数据。")

    # 4. 资源安全回收
    await dedup.close()
    await db_pipeline.close()
    logger.info("=== 学术数据管道任务执行完毕，所有资源已安全释放 ===")

if __name__ == "__main__":
    try:
        asyncio.run(run_pipeline())
    except KeyboardInterrupt:
        logger.info("收到中断指令，任务平滑终止。")