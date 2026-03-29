# config.py
import os

class Config:
    """项目配置"""
    
    # 项目根目录
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 数据目录
    DATA_DIR = os.path.join(BASE_DIR, "data")
    PDF_DIR = os.path.join(DATA_DIR, "pdfs")
    REPORT_DIR = os.path.join(DATA_DIR, "reports")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    
    # arXiv API配置
    ARXIV_API_URL = "http://export.arxiv.org/api/query"
    
    # 下载配置
    DOWNLOAD_CONFIG = {
        'max_results': 50,
        'days_back': 7,
        'sort_by': 'submittedDate',
        'sort_order': 'descending'
    }
    
    # 关键词文件路径
    KEYWORDS_FILE = os.path.join(DATA_DIR, "keywords.txt")
    
    # 邮件配置（从环境变量读取，用于GitHub Actions）
    EMAIL_CONFIG = {
        'enabled': True,
        'smtp_server': 'smtp.qq.com',  # QQ邮箱SMTP服务器
        'smtp_port': 587,
        'sender_email': os.environ.get('SENDER_EMAIL', ''),
        'sender_password': os.environ.get('SENDER_PASSWORD', ''),  # QQ邮箱授权码
        'receiver_email': os.environ.get('RECEIVER_EMAIL', '')
    }

settings = Config()

# 创建必要的目录
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.PDF_DIR, exist_ok=True)
os.makedirs(settings.REPORT_DIR, exist_ok=True)
os.makedirs(settings.LOG_DIR, exist_ok=True)