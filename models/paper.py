import os
import sys

# 动态将项目根目录添加至 sys.path，解决 Windows 环境及 Uvicorn 多进程 reload 时的模块导入问题
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, String, Text, JSON
from core.database import Base


class StandardPaper(BaseModel):
    """
    全平台统一学术论文数据模型（用于数据清洗校验与 API 接口传输）
    """
    paper_id: str                            # 唯一标识 ID（如 "2401.12345" 或 "10.1000/182"）
    title: str                               # 论文标题
    authors: List[str]                       # 作者列表
    abstract: str                            # 论文摘要
    categories: List[str] = Field(default_factory=list)  # 分类标签（如 ["cs.AI", "cs.CL"]）
    published_at: Optional[str] = None      # 发布时间
    updated_at: Optional[str] = None        # 更新时间
    source: str                              # 数据源标识（如 "arxiv", "crossref"）
    url: str                                 # 原文链接
    doi: Optional[str] = None               # 数字对象标识符

    def to_dict(self) -> dict:
        """转换为标准字典，方便序列化与数据库写入"""
        return self.model_dump()


class Paper(Base):
    """
    SQLAlchemy 数据库表模型（映射数据库中的 papers 表，供 FastAPI 查询与写入）
    """
    __tablename__ = "papers"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    authors = Column(JSON, nullable=False)
    abstract = Column(Text, nullable=True)
    categories = Column(JSON, nullable=True)
    published_at = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)
    source = Column(String, index=True, nullable=False)
    url = Column(String, nullable=True)
    doi = Column(String, nullable=True)

    def to_dict(self) -> dict:
        """数据库 ORM 对象转字典，供 API 响应序列化返回"""
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "categories": self.categories,
            "published_at": self.published_at,
            "updated_at": self.updated_at,
            "source": self.source,
            "url": self.url,
            "doi": self.doi
        }