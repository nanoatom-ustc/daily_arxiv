# src/report_generator.py
import os
import logging
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Markdown报告生成器"""
    
    def __init__(self):
        self.report_dir = settings.REPORT_DIR
        os.makedirs(self.report_dir, exist_ok=True)
    
    def generate_markdown(self, papers, keywords, date_str=None):
        """生成Markdown报告"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        report_file = os.path.join(self.report_dir, f"arxiv_report_{date_str}.md")
        
        logger.info(f"生成Markdown报告: {report_file}")
        
        markdown_content = self._create_markdown_content(papers, keywords, date_str)
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Markdown报告保存成功: {report_file}")
            return report_file
            
        except Exception as e:
            logger.error(f"保存Markdown报告失败: {e}")
            return None
    
    def _create_markdown_content(self, papers, keywords, date_str):
        """创建Markdown内容"""
        total_papers = len(papers)
        papers_with_pdf = sum(1 for paper in papers if paper.get('pdf_url'))
        
        # 按分类统计
        category_stats = {}
        for paper in papers:
            for category in paper['categories']:
                category_stats[category] = category_stats.get(category, 0) + 1
        
        content = []
        
        # 标题
        content.append(f"# arXiv论文日报 - {date_str}")
        content.append("")
        content.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"**搜索关键词**: {', '.join(keywords)}")
        content.append(f"**总计论文**: {total_papers} 篇")
        content.append(f"**可下载PDF**: {papers_with_pdf} 篇")
        content.append("")
        
        # 目录
        content.append("## 📋 目录")
        content.append("")
        content.append("- [论文列表](#论文列表)")
        if category_stats:
            content.append("- [分类统计](#分类统计)")
        content.append("- [关键词匹配分析](#关键词匹配分析)")
        content.append("")
        
        # 分类统计
        if category_stats:
            content.append("## 📊 分类统计")
            content.append("")
            content.append("| 分类 | 论文数量 |")
            content.append("|------|----------|")
            for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)[:15]:
                content.append(f"| `{category}` | {count} |")
            content.append("")
        
        # 论文列表
        content.append("## 📄 论文列表")
        content.append("")
        
        if not papers:
            content.append("> 今日未找到相关论文")
            return "\n".join(content)
        
        for i, paper in enumerate(papers, 1):
            content.append(f"### {i}. {paper['title']}")
            content.append("")
            
            # 基本信息
            content.append(f"- **arXiv ID**: `{paper['id']}`")
            content.append(f"- **提交日期**: {paper['published'][:10]}")
            content.append(f"- **作者**: {', '.join(paper['authors'][:5])}" + 
                          (f" 等 {len(paper['authors'])} 人" if len(paper['authors']) > 5 else ""))
            content.append(f"- **分类**: {', '.join(paper['categories'])}")
            content.append(f"- **PDF**: [下载]({paper['pdf_url']})")
            content.append("")
            
            # 摘要
            content.append("**摘要:**")
            content.append("")
            summary = paper['summary'][:500]
            content.append(f"> {summary}..." if len(paper['summary']) > 500 else f"> {summary}")
            content.append("")
            
            # 关键词匹配
            matched = self._find_matched_keywords(paper, keywords)
            if matched:
                content.append(f"**匹配关键词**: {', '.join(matched)}")
                content.append("")
            
            content.append("---")
            content.append("")
        
        # 关键词匹配分析
        content.append("## 🔍 关键词匹配分析")
        content.append("")
        content.append("| 关键词 | 匹配论文数 | 匹配率 |")
        content.append("|--------|------------|--------|")
        
        for keyword in keywords:
            matched_count = sum(1 for paper in papers if self._is_keyword_matched(paper, keyword))
            match_rate = (matched_count / total_papers * 100) if total_papers > 0 else 0
            bar = "█" * int(match_rate / 5) + "░" * (20 - int(match_rate / 5))
            content.append(f"| `{keyword}` | {matched_count} | {match_rate:.1f}% {bar} |")
        
        content.append("")
        
        return "\n".join(content)
    
    def _find_matched_keywords(self, paper, keywords):
        """找出论文匹配的关键词"""
        matched = []
        text = f"{paper['title']} {paper['summary']}".lower()
        
        for keyword in keywords:
            if keyword.lower() in text:
                matched.append(keyword)
        
        return matched
    
    def _is_keyword_matched(self, paper, keyword):
        """检查论文是否匹配特定关键词"""
        text = f"{paper['title']} {paper['summary']}".lower()
        return keyword.lower() in text
    
    def generate_daily_summary(self, papers, keywords):
        """生成每日摘要报告（简版）"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        summary_file = os.path.join(self.report_dir, f"daily_summary_{date_str}.md")
        
        content = []
        content.append(f"# arXiv每日摘要 - {date_str}")
        content.append("")
        content.append(f"**发现论文**: {len(papers)} 篇")
        content.append(f"**关键词**: {', '.join(keywords)}")
        content.append("")
        
        if not papers:
            content.append("## 📭 今日无新论文")
        else:
            content.append("## 🏆 今日精选")
            content.append("")
            
            for i, paper in enumerate(papers[:5], 1):
                content.append(f"### {i}. {paper['title'][:80]}")
                content.append("")
                content.append(f"- **ID**: `{paper['id']}`")
                content.append(f"- **作者**: {paper['authors'][0]}")
                content.append(f"- **摘要**: {paper['summary'][:150]}...")
                content.append("")
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(content))
            
            logger.info(f"每日摘要保存成功: {summary_file}")
            return summary_file
            
        except Exception as e:
            logger.error(f"保存每日摘要失败: {e}")
            return None