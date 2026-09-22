import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert

logger = logging.getLogger(__name__)

# 定义 ORM 基类
class Base(DeclarativeBase):
    pass

# 定义学术论文数据表模型
class PaperModel(Base):
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, comment="论文 Unique ID / DOI")
    title: Mapped[str] = mapped_column(String(512), nullable=False, comment="论文标题")
    authors: Mapped[str] = mapped_column(Text, nullable=True, comment="作者列表")
    abstract: Mapped[str] = mapped_column(Text, nullable=True, comment="摘要")
    url: Mapped[str] = mapped_column(String(512), nullable=True, comment="源链接")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), comment="采集落库时间")

class DataPipeline:
    """
    异步数据持久化管道
    支持基于 SQLAlchemy 2.0 的异步 ORM 操作与 Upsert 幂等落库
    """
    def __init__(self, db_url: str = "sqlite+aiosqlite:///./academic_data.db"):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def init_db(self):
        """初始化数据库表结构"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库初始化完成，数据表结构准备就绪。")

    async def process_item(self, item: Dict[str, Any]) -> bool:
        """
        单条数据处理与 Upsert 幂等落库
        """
        if not item or "id" not in item:
            logger.warning("跳过无效数据项: 缺失主键 ID")
            return False

        async with self.async_session() as session:
            async with session.begin():
                # 使用 SQLite/PostgreSQL 风格的 UPSERT 保证幂等性
                stmt = sqlite_upsert(PaperModel).values(
                    id=item["id"],
                    title=item.get("title", ""),
                    authors="; ".join(item.get("authors", [])) if isinstance(item.get("authors"), list) else item.get("authors", ""),
                    abstract=item.get("abstract", ""),
                    url=item.get("url", "")
                )
                # 当主键冲突时进行更新
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "title": stmt.excluded.title,
                        "authors": stmt.excluded.authors,
                        "abstract": stmt.excluded.abstract,
                        "url": stmt.excluded.url,
                    }
                )
                await session.execute(stmt)
            await session.commit()
            logger.debug(f"数据成功落库/更新: {item['id']}")
            return True

    async def close(self):
        """释放数据库连接池"""
        await self.engine.dispose()