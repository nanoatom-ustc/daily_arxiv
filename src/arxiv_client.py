# src/arxiv_client.py
import requests
import feedparser
from datetime import datetime, timedelta
import logging
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class ArxivClient:
    """arXiv API客户端"""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        # 创建自定义session
        self.session = requests.Session()
        self.session.verify = False  # 禁用SSL验证
        self.session.allow_redirects = False  # 禁止自动重定向到HTTPS
        # 设置超时和重试
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_papers(self, keywords, max_results=50, days_back=7, specific_date=None, categories=None):
        """
        搜索arXiv论文
        
        Args:
            keywords: 关键词列表
            max_results: 最大结果数
            days_back: 回溯天数
            specific_date: 指定日期 (YYYY-MM-DD)
            categories: 分类列表，如 ['physics', 'quant-ph']，默认 None 表示不过滤
        
        Returns:
            论文列表
        """
        query_parts = []
        
        # 构建关键词查询
        if keywords:
            keyword_parts = []
            for keyword in keywords:
                if ' ' in keyword:
                    keyword_parts.append(f'all:"{keyword}"')
                else:
                    keyword_parts.append(f'all:{keyword}')
            if keyword_parts:
                query_parts.append(f"({' OR '.join(keyword_parts)})")
        
        # 添加分类过滤
        if categories:
            cat_parts = [f'cat:{cat}' for cat in categories]
            query_parts.append(f"({' OR '.join(cat_parts)})")
        
        # 如果没有关键词也没有分类，搜索所有
        if not query_parts:
            query_str = "all:1"
        else:
            query_str = " AND ".join(query_parts)
        
        # 计算日期范围
        if specific_date:
            date_obj = datetime.strptime(specific_date, '%Y-%m-%d')
            start_date = date_obj.replace(hour=0, minute=0, second=0)
            end_date = date_obj.replace(hour=23, minute=59, second=59)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
        
        # 构建日期过滤
        date_filter = f"submittedDate:[{start_date.strftime('%Y%m%d')}0000 TO {end_date.strftime('%Y%m%d')}2359]"
        full_query = f"({query_str}) AND {date_filter}"
        
        # 构建查询参数
        params = {
            'search_query': full_query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        logger.info(f"搜索查询: {full_query[:200]}...")
        
        try:
            # 使用 session 发送请求，增加超时时间
            response = self.session.get(self.base_url, params=params, timeout=120)
            
            # 如果被重定向，记录日志
            if response.status_code in [301, 302, 307, 308]:
                logger.warning(f"请求被重定向到: {response.headers.get('Location', 'unknown')}")
                # 尝试直接使用重定向后的URL但使用HTTP
                if 'https' in response.headers.get('Location', ''):
                    # 如果重定向到HTTPS，尝试替换回HTTP
                    alt_url = response.headers['Location'].replace('https://', 'http://')
                    logger.info(f"尝试使用替代URL: {alt_url}")
                    response = self.session.get(alt_url, params=params, timeout=120)
            
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            papers = []
            
            for entry in feed.entries:
                paper = {
                    'id': entry.id.split('/')[-1],
                    'title': self._clean_text(entry.title),
                    'summary': self._clean_text(entry.summary),
                    'authors': [author.name for author in entry.authors],
                    'published': entry.published,
                    'updated': entry.get('updated', entry.published),
                    'categories': [tag.term for tag in entry.tags],
                    'pdf_url': None,
                    'arxiv_url': entry.link
                }
                
                # 查找PDF链接
                for link in entry.links:
                    if link.get('type') == 'application/pdf':
                        paper['pdf_url'] = link.href
                        break
                
                # 如果没有找到PDF链接，构造一个
                if not paper['pdf_url']:
                    paper['pdf_url'] = f"https://arxiv.org/pdf/{paper['id']}.pdf"
                
                papers.append(paper)
            
            logger.info(f"找到 {len(papers)} 篇论文")
            return papers
            
        except requests.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return []
        except Exception as e:
            logger.error(f"解析数据失败: {e}")
            return []
    
    def _clean_text(self, text):
        """清理文本中的换行符和多余空格"""
        return ' '.join(text.replace('\n', ' ').split())