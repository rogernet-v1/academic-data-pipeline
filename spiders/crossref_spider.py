import logging
import httpx
from typing import List, Dict, Any

from spiders.base_spider import BaseSpider
from models.paper import StandardPaper

logger = logging.getLogger(__name__)


class CrossrefSpider(BaseSpider):
    """
    Crossref 学术数据异步采集与解析器
    官方 REST API: https://api.crossref.org/works
    """
    source_name: str = "crossref"
    BASE_URL = "https://api.crossref.org/works"

    async def fetch_papers(self, search_query: str = "artificial intelligence", max_results: int = 10) -> List[StandardPaper]:
        """
        异步请求 Crossref API 并解析返回标准化论文列表
        """
        params = {
            "query": search_query,
            "rows": max_results,
            "sort": "published",
            "order": "desc"
        }

        # Crossref 推荐在 User-Agent 中加入联系邮箱以进入 Polite Pool，享受更高限流额度
        headers = {
            "User-Agent": "AcademicPlatformPipeline/1.0 (mailto:academic_dev@example.com)"
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                logger.info(f"[{self.source_name}] 正在发起 API 异步请求: query={search_query}, rows={max_results}")
                response = await client.get(self.BASE_URL, params=params, headers=headers)
                response.raise_for_status()
                return self.parse(response.json())
            except Exception as e:
                logger.error(f"[{self.source_name}] 数据抓取异常: {e}")
                return []

    def parse(self, raw_data: Dict[str, Any]) -> List[StandardPaper]:
        """
        解析 Crossref JSON 响应，转换为 StandardPaper 标准模型
        """
        papers: List[StandardPaper] = []
        try:
            items = raw_data.get("message", {}).get("items", [])
            for item in items:
                # 使用 DOI 作为 Crossref 的唯一标识
                doi = item.get("DOI")
                if not doi:
                    continue

                # 提取标题
                titles = item.get("title", [])
                title = titles[0].strip() if titles else "Untitled"

                # 提取作者列表
                authors = []
                for author in item.get("author", []):
                    given = author.get("given", "")
                    family = author.get("family", "")
                    name = f"{given} {family}".strip()
                    if name:
                        authors.append(name)

                # 提取摘要（部分文献存在）
                abstract = item.get("abstract", "").replace("\n", " ").strip()

                # 分类标签（Crossref 中的 subject/container-title）
                categories = item.get("subject", [])

                # 发布时间解析
                published_dates = item.get("published", {}).get("date-parts", [[]])
                published_at = None
                if published_dates and published_dates[0]:
                    parts = published_dates[0]
                    published_at = "-".join(f"{p:02d}" for p in parts)

                url = item.get("URL") or f"https://doi.org/{doi}"

                # 构建 StandardPaper 统一模型
                paper = StandardPaper(
                    paper_id=doi,               # 使用 DOI 作为主键 ID
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    categories=categories,
                    published_at=published_at,
                    updated_at=None,
                    source=self.source_name,
                    url=url,
                    doi=doi
                )
                papers.append(paper)

            logger.info(f"[{self.source_name}] 成功解析 {len(papers)} 条标准化论文数据。")
        except Exception as e:
            logger.error(f"[{self.source_name}] JSON 结构化解析失败: {e}")

        return papers