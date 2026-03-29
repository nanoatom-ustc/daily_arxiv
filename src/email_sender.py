# src/email_sender.py
import smtplib
import logging
import re  # 移到文件顶部
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)


class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        self.config = settings.EMAIL_CONFIG
    
    def send_daily_summary(self, summary_content, date_str=None):
        """发送每日摘要邮件"""
        if not self.config['enabled']:
            logger.info("邮件功能未启用")
            return False
        
        if not self.config['sender_email'] or not self.config['sender_password']:
            logger.warning("邮件配置不完整，请设置环境变量 SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL")
            return False
        
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['sender_email']
            msg['To'] = self.config['receiver_email']
            msg['Subject'] = Header(f'arXiv论文日报 - {date_str}', 'utf-8')
            
            html_content = self._markdown_to_html(summary_content)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls()
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.send_message(msg)
            
            logger.info(f"每日摘要邮件发送成功: {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    def _markdown_to_html(self, markdown_content):
        """简单的Markdown转HTML"""
        lines = markdown_content.split('\n')
        html_lines = []
        in_list = False
        
        html_lines.append('<html><head>')
        html_lines.append('<meta charset="UTF-8">')
        html_lines.append('<style>')
        html_lines.append('body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }')
        html_lines.append('h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }')
        html_lines.append('h2 { color: #34495e; margin-top: 25px; }')
        html_lines.append('h3 { color: #555; }')
        html_lines.append('a { color: #3498db; text-decoration: none; }')
        html_lines.append('a:hover { text-decoration: underline; }')
        html_lines.append('pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }')
        html_lines.append('code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }')
        html_lines.append('blockquote { border-left: 3px solid #3498db; padding-left: 15px; color: #666; }')
        html_lines.append('hr { border: none; border-top: 1px solid #ddd; margin: 20px 0; }')
        html_lines.append('</style>')
        html_lines.append('</head><body>')
        
        for line in lines:
            if line.startswith('# '):
                html_lines.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html_lines.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('- '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{line[2:]}</li>')
            elif line.startswith('> '):
                html_lines.append(f'<blockquote>{line[2:]}</blockquote>')
            elif line.startswith('|'):
                if '|--|' in line or '|---|' in line:
                    continue
                html_lines.append(f'<pre>{line}</pre>')
            elif line.startswith('---'):
                html_lines.append('<hr>')
            elif line.strip() == '':
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('<br>')
            elif line.startswith('[') and '](' in line:
                link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
                line = re.sub(link_pattern, r'<a href="\2">\1</a>', line)
                html_lines.append(f'<p>{line}</p>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<p>{line}</p>')
        
        if in_list:
            html_lines.append('</ul>')
        
        html_lines.append('</body></html>')
        
        return '\n'.join(html_lines)