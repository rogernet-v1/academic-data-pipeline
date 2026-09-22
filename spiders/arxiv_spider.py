import logging
import httpx
from xml.etree import ElementTree as ET
from typing import List, Dict, Any
from utils.signer import RequestSigner

logger = logging.getLogger(__name__)

class ArxivSpider:
    """
    ArXiv 学术数据异步采集与解析器
    结合异步 HTTP 客户端与逆向签名校验
    """
    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self):
        self.signer = RequestSigner()

    async def fetch_papers(self, search_query: str = "cat:cs.AI", max_results: int = 10) -> List[Dict[str, Any]]:
        """
        异步请求 arXiv API 并解析论文元数据
        """
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }

        # 生成带有逆向签名的 Headers (用于演示安全反爬绕过)
        headers = self.signer.sign_request(search_query)

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                logger.info(f"正在发起学术 API 异步请求: query={search_query}, max_results={max_results}")
                response = await client.get(self.BASE_URL, params=params, headers=headers)
                response.raise_for_status()
                return self._parse_xml(response.text)
            except Exception as e:
                logger.error(f"ArXiv 数据抓取异常: {e}")
                return []

    def _parse_xml(self, xml_data: str) -> List[Dict[str, Any]]:
        """
        解析 arXiv Atom XML 响应，清洗提取结构化字段
        """
        papers = []
        ns = {"atom": "http://www.w3.org/2005/Atom"}
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

                papers.append({
                    "id": paper_id,
                    "title": title,
                    "authors": authors,
                    "abstract": summary,
                    "url": raw_id
                })
            logger.info(f"成功解析 {len(papers)} 条学术论文结构化数据。")
        except Exception as e:
            logger.error(f"XML 结构化解析失败: {e}")
        return papers