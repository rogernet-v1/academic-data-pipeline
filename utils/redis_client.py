import logging
from typing import Optional, List, Union
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

class RedisDeduplicator:
    """
    基于 Redis 异步连接池的数据去重与增量状态管理器
    """
    def __init__(
        self, 
        redis_url: str = "redis://localhost:6379/0", 
        key_prefix: str = "academic_pipeline:dup:"
    ):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.client: Optional[aioredis.Redis] = None

    async def connect(self):
        """建立 Redis 异步连接池"""
        try:
            self.client = aioredis.from_url(
                self.redis_url, 
                encoding="utf-8", 
                decode_responses=True
            )
            await self.client.ping()
            logger.info("Redis 去重客户端连接成功。")
        except Exception as e:
            logger.warning(f"Redis 连接失败，去重功能将降级为内存模式: {e}")
            self.client = None

    async def is_duplicate(self, task_name: str, item_id: str) -> bool:
        """
        检查 item_id 是否已存在（排重）
        """
        if not self.client:
            return False  # 降级模式，不拦截
        
        key = f"{self.key_prefix}{task_name}"
        try:
            is_member = await self.client.sismember(key, item_id)
            return bool(is_member)
        except Exception as e:
            logger.error(f"Redis 校验去重状态失败 [{item_id}]: {e}")
            return False

    async def add_item(self, task_name: str, item_id: str) -> bool:
        """
        将已成功处理的 item_id 存入 Redis 去重集合
        """
        if not self.client:
            return False

        key = f"{self.key_prefix}{task_name}"
        try:
            await self.client.sadd(key, item_id)
            logger.debug(f"成功将 ID [{item_id}] 加入 Redis 去重集合: {key}")
            return True
        except Exception as e:
            logger.error(f"Redis 写入去重集合失败 [{item_id}]: {e}")
            return False

    async def close(self):
        """关闭 Redis 连接"""
        if self.client:
            await self.client.close()
            logger.info("Redis 去重客户端连接已安全释放。")