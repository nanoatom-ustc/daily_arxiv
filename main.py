#!/usr/bin/env python3
# main.py
"""
arXiv每日论文下载器
自动根据关键词下载最新的arXiv论文
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# 添加src目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from config import settings
from arxiv_client import ArxivClient
from report_generator import ReportGenerator
from email_sender import EmailSender


def setup_logging(verbose=False):
    """配置日志"""
    log_file = os.path.join(settings.LOG_DIR, f"arxiv_downloader_{datetime.now().strftime('%Y%m%d')}.log")
    
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def run_search(keywords, days_back=1, max_results=30, categories=None):
    """
    运行搜索任务（不下载PDF）
    """
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("arXiv论文搜索启动（不下载PDF）")
    logger.info(f"搜索最近 {days_back} 天的论文")
    logger.info(f"关键词: {keywords}")
    logger.info(f"分类过滤: {categories if categories else '无'}")
    logger.info("=" * 60)
    
    try:
        arxiv_client = ArxivClient()
        report_generator = ReportGenerator()
        email_sender = EmailSender()
        
        papers = arxiv_client.search_papers(
            keywords=keywords,
            max_results=max_results,
            days_back=days_back,
            categories=categories
        )
        
        if not papers:
            logger.info("没有找到相关论文")
            summary_content = f"# arXiv论文日报\n\n未找到匹配关键词的论文。\n\n关键词: {', '.join(keywords)}"
            if categories:
                summary_content += f"\n分类: {', '.join(categories)}"
            email_sender.send_daily_summary(summary_content)
            return None
        
        # 生成完整Markdown报告
        report_file = report_generator.generate_markdown(papers, keywords)
        
        # 发送完整报告到邮箱
        if report_file and os.path.exists(report_file):
            with open(report_file, 'r', encoding='utf-8') as f:
                report_content = f.read()
            email_sender.send_daily_summary(report_content)
        
        logger.info(f"处理完成！共找到 {len(papers)} 篇论文")
        
        return {
            'papers': papers,
            'count': len(papers)
        }
        
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
        raise


def load_keywords():
    """加载关键词"""
    keywords_file = settings.KEYWORDS_FILE
    try:
        if not os.path.exists(keywords_file):
            # 创建示例关键词文件
            default_keywords = [
                "quantum"
            ]
            with open(keywords_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(default_keywords))
            print(f"创建默认关键词文件: {keywords_file}")
            return default_keywords
        
        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"加载了 {len(keywords)} 个关键词")
        return keywords
        
    except Exception as e:
        logging.error(f"加载关键词失败: {e}")
        return []


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='arXiv论文搜索器（仅摘要，不下载PDF）')
    parser.add_argument('--days', '-d', type=int, default=7, help='回溯天数 (默认: 1)')
    parser.add_argument('--max', '-m', type=int, default=30, help='最大结果数 (默认: 30)')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--category', '-c', action='append', help='指定arXiv分类，可多次使用')
    parser.add_argument('--keyword', '-k', action='append', help='指定关键词，可多次使用（覆盖关键词文件）')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    # 加载关键词（命令行优先）
    if args.keyword:
        keywords = args.keyword
        print(f"使用命令行关键词: {keywords}")
    else:
        keywords = load_keywords()
    
    if not keywords:
        print("警告: 没有设置关键词，将搜索所有论文")
        keywords = []
    
    # 设置分类过滤
    categories = args.category if args.category else None
    if categories:
        print(f"使用分类过滤: {categories}")
    
    # 运行搜索（不下载PDF）
    result = run_search(
        keywords=keywords,
        days_back=args.days,
        max_results=args.max,
        categories=categories
    )
    
    # 显示结果
    if result:
        print("\n" + "=" * 60)
        print("🎉 arXiv论文搜索完成！")
        print("=" * 60)
        print(f"📅 回溯天数: {args.days} 天")
        print(f"📄 论文数量: {result['count']} 篇")
        if categories:
            print(f"🏷️  分类过滤: {', '.join(categories)}")
        print(f"📁 数据目录: {settings.DATA_DIR}")
        print(f"📄 报告目录: {settings.REPORT_DIR}")
        print("📧 摘要已发送到邮箱")
        print("=" * 60)


if __name__ == "__main__":
    main()
