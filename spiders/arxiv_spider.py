import logging
import httpx
from xml.etree import ElementTree as ET
from typing import List, Dict, Any

from spiders.base_spider import BaseSpider
from models.paper import StandardPaper
from utils.signer import RequestSigner

logger = logging.getLogger(__name__)


class ArxivSpider(BaseSpider):
    """
    ArXiv 学术数据异步采集与解析器（标准化版）
    """
    source_name: str = "arxiv"
    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self, timeout: float = 15.0):
        super().__init__(timeout=timeout)
        self.signer = RequestSigner()

    async def fetch_papers(self, search_query: str = "cat:cs.AI", max_results: int = 10) -> List[StandardPaper]:
        """
        异步请求 arXiv API 并解析返回标准化论文列表
        """
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }

        # 生成带有逆向签名的 Headers
        headers = self.signer.sign_request(search_query)

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                logger.info(f"[{self.source_name}] 正在发起 API 异步请求: query={search_query}, max_results={max_results}")
                response = await client.get(self.BASE_URL, params=params, headers=headers)
                response.raise_for_status()
                return self.parse(response.text)
            except Exception as e:
                logger.error(f"[{self.source_name}] 数据抓取异常: {e}")
                return []

    def parse(self, xml_data: str) -> List[StandardPaper]:
        """
        解析 arXiv Atom XML 响应，转换为 StandardPaper 标准模型
        """
        papers: List[StandardPaper] = []
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

        try:
            root = ET.fromstring(xml_data)
            for entry in root.findall("atom:entry", ns):
                raw_id = entry.findtext("atom:id", "", ns)
                paper_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id

                title = entry.findtext("atom:title", "", ns).replace("\n", " ").strip()
                summary = entry.findtext("atom:summary", "", ns).replace("\n", " ").strip()

                authors = [
                    author.findtext("atom:name", "", ns)
                    for author in entry.findall("atom:author", ns)
                ]

                # 提取分类 categories
                categories = [
                    cat.get("term")
                    for cat in entry.findall("atom:category", ns)
                    if cat.get("term")
                ]

                # 时间提取
                published = entry.findtext("atom:published", "", ns)
                updated = entry.findtext("atom:updated", "", ns)

                # DOI (若存在)
                doi_elem = entry.find("arxiv:doi", ns)
                doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None

                # 构建标准化 StandardPaper 对象
                paper = StandardPaper(
                    paper_id=paper_id,
                    title=title,
                    authors=authors,
                    abstract=summary,
                    categories=categories,
                    published_at=published,
                    updated_at=updated,
                    source=self.source_name,
                    url=f"https://arxiv.org/abs/{paper_id}",
                    doi=doi
                )
                papers.append(paper)

            logger.info(f"[{self.source_name}] 成功解析 {len(papers)} 条标准化论文数据。")
        except Exception as e:
            logger.error(f"[{self.source_name}] XML 结构化解析失败: {e}")

        return papers