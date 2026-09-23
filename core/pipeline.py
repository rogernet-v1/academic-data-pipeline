import logging
from typing import Dict, Any, List, Union
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert

from models.paper import StandardPaper

logger = logging.getLogger(__name__)


# 定义 ORM 基类
class Base(DeclarativeBase):
    pass


# 定义标准学术论文数据表模型
class PaperModel(Base):
    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(128), primary_key=True, comment="论文 Unique ID / DOI")
    title: Mapped[str] = mapped_column(String(512), nullable=False, comment="论文标题")
    authors: Mapped[str] = mapped_column(Text, nullable=True, comment="作者列表（分号分隔）")
    abstract: Mapped[str] = mapped_column(Text, nullable=True, comment="摘要")
    categories: Mapped[str] = mapped_column(String(256), nullable=True, comment="分类标签（分号分隔）")
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown", comment="数据源标识")
    url: Mapped[str] = mapped_column(String(512), nullable=True, comment="源链接")
    doi: Mapped[str] = mapped_column(String(128), nullable=True, comment="数字对象标识符")
    published_at: Mapped[str] = mapped_column(String(64), nullable=True, comment="发布时间")
    updated_at: Mapped[str] = mapped_column(String(64), nullable=True, comment="更新时间")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), comment="采集落库时间")


class DataPipeline:
    """
    异步数据持久化管道
    支持基于 SQLAlchemy 2.0 的异步 ORM 操作与 StandardPaper 标准模型 Upsert 幂等落库
    """
    def __init__(self, db_url: str = "sqlite+aiosqlite:///./academic_data.db"):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def init_db(self):
        """初始化数据库表结构"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库初始化完成，数据表结构准备就绪。")

    def _convert_to_dict(self, paper: Union[StandardPaper, Dict[str, Any]]) -> dict:
        """将 StandardPaper 或字典统一转换为 ORM 所需的平铺字典"""
        if isinstance(paper, StandardPaper):
            p = paper.to_dict()
        else:
            p = paper

        authors_str = "; ".join(p.get("authors", [])) if isinstance(p.get("authors"), list) else p.get("authors", "")
        categories_str = "; ".join(p.get("categories", [])) if isinstance(p.get("categories"), list) else p.get("categories", "")

        return {
            "id": p.get("paper_id") or p.get("id"),
            "title": p.get("title", ""),
            "authors": authors_str,
            "abstract": p.get("abstract", ""),
            "categories": categories_str,
            "source": p.get("source", "unknown"),
            "url": p.get("url", ""),
            "doi": p.get("doi"),
            "published_at": p.get("published_at"),
            "updated_at": p.get("updated_at")
        }

    async def process_item(self, item: Union[StandardPaper, Dict[str, Any]]) -> bool:
        """
        单条数据处理与 Upsert 幂等落库
        """
        data = self._convert_to_dict(item)
        if not data["id"]:
            logger.warning("跳过无效数据项: 缺失主键 ID")
            return False

        async with self.async_session() as session:
            async with session.begin():
                stmt = sqlite_upsert(PaperModel).values(**data)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "title": stmt.excluded.title,
                        "authors": stmt.excluded.authors,
                        "abstract": stmt.excluded.abstract,
                        "categories": stmt.excluded.categories,
                        "source": stmt.excluded.source,
                        "url": stmt.excluded.url,
                        "doi": stmt.excluded.doi,
                        "published_at": stmt.excluded.published_at,
                        "updated_at": stmt.excluded.updated_at,
                    }
                )
                await session.execute(stmt)
            await session.commit()
            logger.debug(f"数据成功落库/更新: {data['id']}")
            return True

    async def close(self):
        """释放数据库连接池"""
        await self.engine.dispose()