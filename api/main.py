import os
import sys
from typing import Optional
from fastapi import FastAPI, Query, HTTPException, Depends
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

# 确保能正常导入项目根目录模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.paper import Paper
from core.database import AsyncSessionLocal

app = FastAPI(
    title="学术论文采集与分析平台 API",
    description="提供多数据源（arXiv, Crossref）学术论文数据的检索、筛选与统计服务",
    version="1.0.0"
)


# 依赖项：获取数据库异步 Session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@app.get("/", tags=["基础"])
async def root():
    return {
        "status": "online",
        "message": "学术论文数据 API 服务运行中",
        "docs_url": "/docs"
    }


@app.get("/api/v1/papers", tags=["论文检索"])
async def list_papers(
    source: Optional[str] = Query(None, description="按数据源筛选，例如 arxiv / crossref"),
    keyword: Optional[str] = Query(None, description="按标题或摘要关键字模糊搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    分页查询已落库论文，支持按来源筛选与关键词搜索
    """
    query = select(Paper)

    # 1. 来源筛选
    if source:
        query = query.where(Paper.source == source.lower())

    # 2. 关键词模糊检索
    if keyword:
        pattern = f"%{keyword}%"
        query = query.where(
            (Paper.title.ilike(pattern)) | (Paper.abstract.ilike(pattern))
        )

    # 3. 统计符合条件的总条数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 4. 执行分页与排序（按发布时间倒序）
    offset = (page - 1) * page_size
    query = query.order_by(Paper.published_at.desc()).offset(offset).limit(page_size)

    result = await db.execute(query)
    papers = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [paper.to_dict() for paper in papers]
    }


@app.get("/api/v1/papers/{paper_id:path}", tags=["论文检索"])
async def get_paper_detail(
    paper_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    按论文 ID / DOI 查询详情
    """
    query = select(Paper).where(Paper.id == paper_id)
    result = await db.execute(query)
    paper = result.scalars().first()

    if not paper:
        raise HTTPException(status_code=404, detail=f"未找到 ID 为 '{paper_id}' 的论文记录")

    return {"data": paper.to_dict()}


@app.get("/api/v1/stats", tags=["统计分析"])
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    数据源收录量统计接口
    """
    # 按 source 分组统计数量
    query = select(Paper.source, func.count(Paper.id)).group_by(Paper.source)
    result = await db.execute(query)
    source_stats = {source: count for source, count in result.all()}

    # 总论文数
    total_query = select(func.count(Paper.id))
    total_result = await db.execute(total_query)
    total_count = total_result.scalar() or 0

    return {
        "total_papers": total_count,
        "by_source": source_stats
    }