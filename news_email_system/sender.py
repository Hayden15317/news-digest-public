"""
邮件发送模块 - 负责生成和发送HTML邮件
"""

import logging
import os
import smtplib
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from email.utils import formataddr
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from typing import Dict, List, Optional

from fetcher import NewsItem
from config import (
    CATEGORY_DISPLAY_ORDER,
    PUBLIC_REPORT_SITE_URL,
    SMTP_PORT,
    SMTP_SERVER,
    SMTP_USE_SSL,
    SENDER_EMAIL,
    SENDER_NAME,
    SENDER_PASSWORD,
    RECIPIENT_EMAILS,
    SUBCATEGORY_DISPLAY_ORDER,
)

logger = logging.getLogger(__name__)

LOCAL_REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
PUBLIC_REPORTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "reports")
)

ANCHOR_SLUG_MAP = {
    "top": "top",
    "all-news": "all-news",
    "总新闻数": "all-news",
    "行业新闻": "industry-news",
    "金融新闻": "finance-news",
    "时政新闻": "current-affairs-news",
    "其他": "other-news",
    "基金TA": "fund-ta",
    "基金": "funds",
    "证券": "securities",
    "A股": "a-share",
    "港股": "hk-share",
    "行情": "market",
    "宏观经济": "macro",
    "利率": "rates",
    "汇率": "fx",
    "民生": "livelihood",
    "社会": "society",
    "国务院": "state-council",
    "发改委": "ndrc",
    "央行": "pbc",
    "财政部": "mof",
    "证监会": "csrc",
    "人大": "npc",
}


@dataclass
class EmailDeliveryConfig:
    """邮件投递配置"""

    smtp_server: str = SMTP_SERVER
    smtp_port: int = SMTP_PORT
    use_ssl: bool = SMTP_USE_SSL
    sender_email: str = SENDER_EMAIL
    sender_password: str = SENDER_PASSWORD
    sender_name: str = SENDER_NAME
    recipient_emails: Optional[List[str]] = None
    reply_to: str = ""
    subject_prefix: str = "【广发基金视角晨报】"
    public_report_site_url: str = PUBLIC_REPORT_SITE_URL
    report_slug: str = "latest"

    def __post_init__(self):
        if self.recipient_emails is None:
            self.recipient_emails = [email.strip() for email in RECIPIENT_EMAILS if email.strip()]
        else:
            self.recipient_emails = [email.strip() for email in self.recipient_emails if email.strip()]


class EmailSender:
    """邮件发送器"""

    def __init__(self, delivery_config: Optional[EmailDeliveryConfig] = None):
        self.delivery_config = delivery_config or EmailDeliveryConfig()
        self.smtp_server = self.delivery_config.smtp_server
        self.smtp_port = self.delivery_config.smtp_port
        self.use_ssl = self.delivery_config.use_ssl
        self.sender_email = self.delivery_config.sender_email
        self.sender_password = self.delivery_config.sender_password
        self.sender_name = self.delivery_config.sender_name
        self.recipient_emails = self.delivery_config.recipient_emails
        self.reply_to = self.delivery_config.reply_to
        self.subject_prefix = self.delivery_config.subject_prefix
        self.public_report_site_url = (
            self.delivery_config.public_report_site_url.strip().rstrip("/")
        )
        self.report_slug = self._normalize_report_slug(self.delivery_config.report_slug)

    def send_news_email(
        self,
        news_items: List[NewsItem],
        date: datetime = None
    ) -> bool:
        """
        发送新闻邮件
        """
        news_items = news_items or []

        if date is None:
            date = datetime.now()

        # 生成邮件内容
        subject = self._generate_subject(date, len(news_items))
        html_content = self._generate_html(news_items, date, navigation_mode="email")

        # 发送邮件
        return self._send_email(subject, html_content, news_items)

    def export_web_report(self, news_items: List[NewsItem], date: datetime = None) -> Dict[str, str]:
        news_items = news_items or []
        if date is None:
            date = datetime.now()

        html_content = self._generate_html(news_items, date, navigation_mode="internal")
        written_paths = []
        for output_path in self._get_report_output_paths():
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(html_content)
            written_paths.append(output_path)

        return {
            "slug": self.report_slug,
            "local_report_url": f"/reports/{self.report_slug}.html",
            "public_report_url": self._build_public_report_url(),
            "written_paths": ", ".join(written_paths),
        }

    def _generate_subject(self, date: datetime, news_count: int) -> str:
        """
        生成邮件主题
        """
        date_str = date.strftime("%Y年%m月%d日")
        return f"{self.subject_prefix}{date_str} - 共{news_count}条新闻"

    def _generate_html(
        self,
        news_items: List[NewsItem],
        date: datetime,
        navigation_mode: str = "email",
    ) -> str:
        """
        生成HTML邮件内容
        """
        news_items = news_items or []
        date_str = date.strftime("%Y年%m月%d日")

        total_count = len(news_items)
        industry_count = len([n for n in news_items if n.category == "行业新闻"])
        finance_count = len([n for n in news_items if n.category == "金融新闻"])
        politics_count = len([n for n in news_items if n.category == "时政新闻"])

        categorized_news = self._organize_by_category(news_items)
        overview_html = self._generate_overview_html(news_items)
        highlights_html = self._generate_top_highlights_html(news_items)
        pulse_html = self._generate_market_pulse_html(news_items)
        source_board_html = self._generate_source_board_html(news_items)
        stats_html = self._generate_stats_html(
            total_count=total_count,
            industry_count=industry_count,
            finance_count=finance_count,
            politics_count=politics_count,
            navigation_mode=navigation_mode,
        )

        if news_items:
            content_html = f'<div id="all-news" name="all-news">{self._generate_category_html(categorized_news)}</div>'
        else:
            content_html = '<div id="all-news" name="all-news"><p style="color:#666;text-align:center;">今日暂无抓取到的新闻</p></div>'

        html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日新闻推送</title>
    <style>
        body {{
            font-family: 'Segoe UI', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: #ffffff;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .header .date {{
            margin-top: 10px;
            font-size: 16px;
            opacity: 0.9;
        }}
        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 20px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        .stat-item {{
            display: block;
            text-align: center;
            text-decoration: none;
            color: inherit;
            padding: 14px 16px;
            border-radius: 18px;
            border: 1px solid #e2e8ff;
            background: linear-gradient(180deg, #ffffff 0%, #f6f8ff 100%);
            box-shadow: 0 4px 14px rgba(69, 89, 164, 0.08);
        }}
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
        }}
        .stat-action {{
            display: inline-block;
            margin-top: 10px;
            padding: 5px 12px;
            border-radius: 999px;
            background: #667eea;
            color: #ffffff;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.02em;
        }}
        .stat-note {{
            margin-top: 8px;
            font-size: 11px;
            color: #8a94ad;
        }}
        .content {{
            padding: 30px;
        }}
        .hero-note {{
            margin-top: 14px;
            font-size: 13px;
            opacity: 0.92;
        }}
        .overview {{
            margin-bottom: 28px;
            padding: 18px 20px;
            border: 1px solid #e7ecff;
            border-radius: 16px;
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
        }}
        .overview-title {{
            font-size: 17px;
            font-weight: 700;
            color: #233876;
            margin-bottom: 10px;
        }}
        .overview-text {{
            font-size: 13px;
            color: #58627a;
            line-height: 1.8;
        }}
        .brief-list {{
            margin: 12px 0 0;
            padding-left: 18px;
            color: #49536a;
            font-size: 13px;
        }}
        .brief-list li {{
            margin-bottom: 6px;
        }}
        .insight-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
            margin-bottom: 28px;
        }}
        .insight-card {{
            padding: 16px;
            border-radius: 16px;
            border: 1px solid #e8ebf5;
            background: #fbfcff;
            box-shadow: 0 4px 18px rgba(69, 89, 164, 0.06);
        }}
        .insight-label {{
            font-size: 12px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #7d88a5;
        }}
        .insight-value {{
            margin-top: 8px;
            font-size: 14px;
            font-weight: 700;
            color: #20336d;
            line-height: 1.7;
        }}
        .highlight-section {{
            margin-bottom: 28px;
        }}
        .section-title-block {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
        }}
        .section-title-text {{
            font-size: 18px;
            font-weight: 700;
            color: #21356d;
        }}
        .section-desc {{
            font-size: 12px;
            color: #6f7b95;
        }}
        .highlight-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 14px;
        }}
        .highlight-card {{
            border: 1px solid #e8ebf5;
            border-radius: 18px;
            padding: 18px;
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            box-shadow: 0 6px 20px rgba(69, 89, 164, 0.08);
        }}
        .highlight-rank {{
            display: inline-block;
            margin-bottom: 10px;
            padding: 4px 10px;
            border-radius: 999px;
            background: #edf2ff;
            color: #4964da;
            font-size: 11px;
            font-weight: 700;
        }}
        .highlight-title {{
            font-size: 16px;
            font-weight: 700;
            line-height: 1.6;
            margin-bottom: 10px;
        }}
        .highlight-title a {{
            color: #20336d;
            text-decoration: none;
        }}
        .highlight-summary {{
            font-size: 13px;
            line-height: 1.8;
            color: #5b667f;
            margin-bottom: 10px;
        }}
        .tag-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 10px;
        }}
        .tag {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 11px;
            color: #435170;
            background: #f1f4fb;
        }}
        .tag.impact {{
            color: #1f4f8b;
            background: #e6f1ff;
        }}
        .why-line {{
            font-size: 12px;
            color: #59657d;
            line-height: 1.7;
            margin-bottom: 10px;
        }}
        .nav-chip {{
            display: inline-block;
            padding: 5px 10px;
            font-size: 12px;
            border-radius: 999px;
            background: #f3f5fb;
            color: #49536a;
            text-decoration: none;
        }}
        .category-section {{
            margin-bottom: 35px;
            scroll-margin-top: 12px;
        }}
        .category-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            margin-bottom: 20px;
        }}
        .category-title {{
            font-size: 20px;
            font-weight: 700;
            color: #333;
        }}
        .category-tools {{
            font-size: 12px;
            color: #667eea;
            text-decoration: none;
            white-space: nowrap;
        }}
        .subcategory-nav {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 16px;
        }}
        .subcategory {{
            margin-bottom: 20px;
            scroll-margin-top: 12px;
        }}
        .subcategory-title {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            font-size: 15px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 12px;
            padding: 10px 12px;
            border-left: 3px solid #667eea;
            background: #f8faff;
            border-radius: 8px;
        }}
        .subcategory-count {{
            color: #7d88a5;
            font-size: 12px;
            font-weight: 600;
        }}
        .news-item {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .news-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .news-title {{
            font-size: 15px;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            line-height: 1.4;
        }}
        .news-title a {{
            color: #333;
            text-decoration: none;
            transition: color 0.2s;
        }}
        .news-title a:hover {{
            color: #667eea;
        }}
        .news-summary {{
            font-size: 13px;
            color: #666;
            line-height: 1.6;
            margin-bottom: 8px;
        }}
        .news-focus {{
            display: inline-flex;
            margin-bottom: 10px;
            padding: 4px 10px;
            border-radius: 999px;
            background: #eef3ff;
            color: #4964da;
            font-size: 11px;
            font-weight: 600;
        }}
        .news-tag-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 10px;
        }}
        .news-meta {{
            font-size: 11px;
            color: #999;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .news-source {{
            font-weight: 500;
        }}
        .news-time {{
            font-style: italic;
        }}
        .source-board {{
            margin-top: 28px;
            padding: 18px 20px;
            border: 1px solid #e7ecff;
            border-radius: 16px;
            background: #fbfcff;
        }}
        .source-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }}
        .source-chip {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: #f2f5fb;
            color: #53607a;
            font-size: 12px;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #e9ecef;
        }}
        .footer-text {{
            font-size: 12px;
            color: #6c757d;
        }}
        @media (max-width: 600px) {{
            .header h1 {{
                font-size: 22px;
            }}
            .content {{
                padding: 20px;
            }}
            .news-item {{
                padding: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>广发基金视角晨报</h1>
            <div class="date">{date_str}</div>
            <div class="hero-note">优先保留与基金投研、资本市场、宏观政策和跨境配置强相关的国内新闻。</div>
        </div>

        <div class="stats">
            {stats_html}
        </div>

        <div class="content">
            {highlights_html}
            <div id="top" name="top" class="overview">{overview_html}</div>
            {pulse_html}
{content_html}
            {source_board_html}
        </div>

        <div class="footer">
            <div class="footer-text">
                此邮件由自动新闻推送系统生成 | 发送时间: {send_time}<br>
                列表时间优先展示新闻真实发布时间，若源站仅提供日期则显示日期信息
            </div>
        </div>
    </div>
</body>
</html>"""

        send_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return html_template.format(
            date_str=date_str,
            content_html=content_html,
            highlights_html=highlights_html,
            overview_html=overview_html,
            pulse_html=pulse_html,
            source_board_html=source_board_html,
            stats_html=stats_html,
            total_count=total_count,
            industry_count=industry_count,
            finance_count=finance_count,
            politics_count=politics_count,
            send_time=send_time
        )

    def _select_highlights(self, news_items: List[NewsItem], limit: int = 4) -> List[NewsItem]:
        ranked = sorted(
            news_items,
            key=lambda item: (item.priority_score, item.relevance_score, item.published),
            reverse=True,
        )
        return ranked[:limit]

    def _generate_top_highlights_html(self, news_items: List[NewsItem]) -> str:
        highlights = self._select_highlights(news_items, limit=3)
        if not highlights:
            return ""

        cards = []
        for index, item in enumerate(highlights, 1):
            title = escape(item.title) if item.title else "无标题"
            has_valid_link = self._is_valid_news_link(item.link)
            link = escape(item.link, quote=True) if has_valid_link else ""
            summary = self._truncate_text(item.summary or item.content or "暂无摘要", 68)
            source = escape(item.source) if item.source else "未知来源"
            meta = f"{escape(item.category)} / {escape(item.subcategory)}"
            time_text = self._format_published(item)
            focus_reason = self._truncate_text(getattr(item, "focus_reason", "") or "", 42)

            cards.append(
                f'''<div class="highlight-card">
    <div class="highlight-rank">重点 {index}</div>
    <div class="highlight-title">{self._render_title_link(title, link)}</div>
    <div class="highlight-summary">{escape(summary)}</div>
    <div class="tag-row">
        <span class="tag">{meta}</span>
        <span class="tag">{source}</span>
    </div>
    {f'<div class="news-focus">{escape(focus_reason)}</div>' if focus_reason else ''}
    <div class="news-meta">
        <span class="news-source">重点筛选</span>
        <span class="news-time">{time_text}</span>
    </div>
</div>'''
            )

        return (
            '<div class="highlight-section">'
            '<div class="section-title-block">'
            '<div>'
            '<div class="section-title-text">顶部重点新闻</div>'
            '<div class="section-desc">按优先级、相关度和发布时间筛出最值得先看的 3 条。</div>'
            '</div>'
            '</div>'
            f'<div class="highlight-grid">{"".join(cards)}</div>'
            '</div>'
        )

    def _generate_overview_html(self, news_items: List[NewsItem]) -> str:
        if not news_items:
            return (
                '<div class="overview-title">今日聚焦</div>'
                '<div class="overview-text">今日暂无抓取到满足基金视角筛选条件的新闻。</div>'
            )

        category_counts = Counter(item.category for item in news_items)
        lead_category = category_counts.most_common(1)[0][0]
        top_tags = self._collect_top_tags(news_items, limit=4)

        bullets = [
            f"今日共筛出 {len(news_items)} 条新闻，其中 {lead_category} 占比最高，适合作为晨会首屏速览。",
            f"当前最值得优先关注的方向包括：{'、'.join(top_tags) if top_tags else '基金发行、资本市场与政策脉络'}。",
        ]

        bullet_html = "".join(f"<li>{bullet}</li>" for bullet in bullets)
        return (
            '<div class="overview-title">今日聚焦</div>'
            '<div class="overview-text">这封邮件优先保留与基金投研、产品发行、市场流动性、宏观政策和港股配置相关的高价值新闻。</div>'
            f'<ol class="brief-list">{bullet_html}</ol>'
        )

    def _generate_market_pulse_html(self, news_items: List[NewsItem]) -> str:
        insights = [
            ("市场主线", "、".join(self._collect_top_tags(news_items, limit=3)) or "重点关注基金、券商、A股和政策信号"),
            ("优先来源", "、".join(self._collect_top_sources(news_items, limit=3)) or "以权威财经和政策来源为主"),
            ("时间窗口", self._build_time_window_text(news_items)),
            ("阅读建议", "按行业、金融、时政分栏快速定位需要深读的条目"),
        ]
        cards = []
        for label, value in insights:
            cards.append(
                f'''<div class="insight-card">
    <div class="insight-label">{escape(label)}</div>
    <div class="insight-value">{escape(value)}</div>
</div>'''
            )
        return f'<div class="insight-grid">{"".join(cards)}</div>'

    def _generate_source_board_html(self, news_items: List[NewsItem]) -> str:
        sources = self._collect_top_sources(news_items, limit=8, with_count=True)
        if not sources:
            return ""
        chips = "".join(
            f'<span class="source-chip">{escape(name)} · {count}</span>'
            for name, count in sources
        )
        return (
            '<div class="source-board">'
            '<div class="overview-title">来源覆盖</div>'
            '<div class="overview-text">保留多来源交叉验证，尽量避免单一站点刷屏，提高晨报可读性与信任感。</div>'
            f'<div class="source-list">{chips}</div>'
            '</div>'
        )

    def _collect_top_sources(self, news_items: List[NewsItem], limit: int = 3, with_count: bool = False):
        counter = Counter(item.source or "未知来源" for item in news_items)
        most_common = counter.most_common(limit)
        if with_count:
            return most_common
        return [name for name, _ in most_common]

    def _collect_top_tags(self, news_items: List[NewsItem], limit: int = 4) -> List[str]:
        counter: Counter = Counter()
        for item in news_items:
            counter.update(self._extract_signal_tags(item))
        return [name for name, _ in counter.most_common(limit)]

    def _extract_signal_tags(self, item: NewsItem) -> List[str]:
        text = " ".join(
            [
                item.title or "",
                item.summary or "",
                item.content or "",
                item.category or "",
                item.subcategory or "",
            ]
        )
        tags = []
        signal_map = [
            ("基金发行", ("基金发行", "新发基金", "ETF", "REITs", "FOF", "QDII")),
            ("机构配置", ("基金经理", "持仓", "申购", "赎回", "机构资金", "仓位")),
            ("券商监管", ("券商", "证券公司", "证监会", "交易所", "IPO", "并购重组")),
            ("A股风格", ("A股", "沪指", "深成指", "北向资金", "融资余额")),
            ("港股配置", ("港股", "恒生", "港股通", "南向资金", "恒生科技")),
            ("货币政策", ("中国人民银行", "LPR", "MLF", "降准", "降息", "逆回购", "社融")),
            ("财政政策", ("财政部", "专项债", "预算", "税收", "国债")),
            ("汇率外资", ("人民币", "汇率", "美元指数", "离岸人民币", "中间价")),
        ]
        for label, keywords in signal_map:
            if any(keyword in text for keyword in keywords):
                tags.append(label)

        if item.category == "行业新闻" and "行业主线" not in tags:
            tags.append("行业主线")
        elif item.category == "金融新闻" and "宏观市场" not in tags:
            tags.append("宏观市场")
        elif item.category == "时政新闻" and "政策信号" not in tags:
            tags.append("政策信号")

        return tags[:4]

    def _build_time_window_text(self, news_items: List[NewsItem]) -> str:
        if not news_items:
            return "暂无新闻"
        earliest = min(item.published for item in news_items)
        latest = max(item.published for item in news_items)
        return f"{earliest.strftime('%m-%d %H:%M')} 至 {latest.strftime('%m-%d %H:%M')}"

    def _truncate_text(self, text: str, limit: int) -> str:
        clean = (text or "").strip()
        if len(clean) <= limit:
            return clean
        return clean[: max(limit - 1, 1)].rstrip() + "…"

    def _format_published(self, item: NewsItem) -> str:
        if item.published.hour == 0 and item.published.minute == 0:
            return item.published.strftime("%Y-%m-%d") + "（仅日期可得）"
        return item.published.strftime("%Y-%m-%d %H:%M")

    def _organize_by_category(
        self,
        news_items: List[NewsItem]
    ) -> Dict[str, Dict[str, List[NewsItem]]]:
        """
        按类别和子类别组织新闻
        """
        organized = {}

        for item in news_items:
            if item.category not in organized:
                organized[item.category] = {}

            if item.subcategory not in organized[item.category]:
                organized[item.category][item.subcategory] = []

            organized[item.category][item.subcategory].append(item)

        return organized

    def _make_anchor_id(self, *parts: str) -> str:
        slug_parts = []
        for part in parts:
            text = (part or "").strip()
            if not text:
                continue
            mapped = ANCHOR_SLUG_MAP.get(text)
            if mapped:
                slug_parts.append(mapped)
                continue

            normalized = []
            for char in text.lower():
                if char.isascii() and char.isalnum():
                    normalized.append(char)
                else:
                    normalized.append("-")
            slug = "".join(normalized).strip("-")
            slug_parts.append(slug or "section")
        return "-".join(slug_parts).strip("-") or "section"

    def _normalize_report_slug(self, value: str) -> str:
        text = (value or "").strip().lower()
        if not text:
            return "latest"

        normalized = []
        for char in text:
            if char.isascii() and char.isalnum():
                normalized.append(char)
            elif char in {"-", "_"}:
                normalized.append("-")
            else:
                normalized.append("-")
        slug = "".join(normalized).strip("-")
        return slug or "latest"

    def _get_report_output_paths(self) -> List[str]:
        report_name = f"{self.report_slug}.html"
        paths = [
            os.path.join(LOCAL_REPORTS_DIR, report_name),
            os.path.join(PUBLIC_REPORTS_DIR, report_name),
        ]
        if self.report_slug != "latest":
            paths.extend(
                [
                    os.path.join(LOCAL_REPORTS_DIR, "latest.html"),
                    os.path.join(PUBLIC_REPORTS_DIR, "latest.html"),
                ]
            )

        unique_paths = []
        seen = set()
        for path in paths:
            normalized = os.path.normpath(path)
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_paths.append(normalized)
        return unique_paths

    def _build_public_report_url(self, anchor: str = "") -> str:
        if not self.public_report_site_url:
            return ""
        anchor_text = (anchor or "").strip()
        if anchor_text and not anchor_text.startswith("#"):
            anchor_text = f"#{anchor_text}"
        return f"{self.public_report_site_url}/reports/{self.report_slug}.html{anchor_text}"

    def _build_navigation_link(self, anchor: str, navigation_mode: str) -> tuple[str, str, str, str]:
        anchor_id = anchor.lstrip("#")
        if navigation_mode == "email":
            public_url = self._build_public_report_url(anchor_id)
            if public_url:
                return (
                    public_url,
                    "_blank",
                    ' rel="noopener noreferrer"',
                    "点击打开公网晨报对应栏目",
                )
        return (f"#{anchor_id}", "_self", "", "点击定位到对应栏目")

    def _generate_stats_html(
        self,
        total_count: int,
        industry_count: int,
        finance_count: int,
        politics_count: int,
        navigation_mode: str = "email",
    ) -> str:
        stat_items = [
            ("all-news", total_count, "总新闻数"),
            (self._make_anchor_id('行业新闻'), industry_count, "行业新闻"),
            (self._make_anchor_id('金融新闻'), finance_count, "金融新闻"),
            (self._make_anchor_id('时政新闻'), politics_count, "时政新闻"),
        ]
        cards = []
        for anchor_id, count, label in stat_items:
            target, html_target, rel_attr, note = self._build_navigation_link(anchor_id, navigation_mode)
            cards.append(
                f'''<a class="stat-item" href="{target}" target="{html_target}"{rel_attr}>
    <div class="stat-number">{count}</div>
    <div class="stat-label">{escape(label)}</div>
    <div class="stat-action">立即查看</div>
    <div class="stat-note">{note}</div>
</a>'''
            )
        return "".join(cards)

    def _category_description(self, category: str) -> str:
        descriptions = {
            "行业新闻": "证券、基金、A股、港股，优先展示基金投研与资本市场动态。",
            "金融新闻": "宏观经济、利率、汇率和市场流动性，辅助判断配置环境。",
            "时政新闻": "央行、财政部等政策与监管信号，补充制度与政策背景。",
            "其他": "未归入核心维度的补充信息。",
        }
        return descriptions.get(category, "分类新闻速览")

    def _generate_category_html(
        self,
        categorized_news: Dict[str, Dict[str, List[NewsItem]]]
    ) -> str:
        """
        生成分类别的HTML内容
        """
        html_parts = []

        for category in CATEGORY_DISPLAY_ORDER:
            if category not in categorized_news:
                continue

            subcategories = categorized_news[category]
            category_anchor = self._make_anchor_id(category)
            ordered_subcategories = SUBCATEGORY_DISPLAY_ORDER.get(category, [])
            sorted_subcategories = sorted(
                subcategories.items(),
                key=lambda pair: (
                    ordered_subcategories.index(pair[0])
                    if pair[0] in ordered_subcategories
                    else len(ordered_subcategories),
                    pair[0],
                )
            )

            html_parts.append(f'<div id="{category_anchor}" name="{category_anchor}" class="category-section">')
            html_parts.append('<div class="category-header">')
            html_parts.append(f'<div class="category-title">{escape(category)}</div>')
            html_parts.append('<a class="category-tools" href="#top" target="_self">返回顶部</a>')
            html_parts.append('</div>')
            html_parts.append('<div class="subcategory-nav">')
            for subcategory, items in sorted_subcategories:
                sub_anchor = self._make_anchor_id(category, subcategory)
                html_parts.append(
                    f'<a class="nav-chip" href="#{sub_anchor}" target="_self">{escape(subcategory)} · {len(items)}</a>'
                )
            html_parts.append('</div>')

            # 按子类别输出
            for subcategory, items in sorted_subcategories:
                if not items:
                    continue

                sub_anchor = self._make_anchor_id(category, subcategory)
                html_parts.append(f'<div id="{sub_anchor}" name="{sub_anchor}" class="subcategory">')
                html_parts.append(
                    f'<div class="subcategory-title"><span>{escape(subcategory)}</span><span class="subcategory-count">{len(items)} 条</span></div>'
                )

                for item in items:
                    news_html = self._generate_news_item_html(item)
                    html_parts.append(news_html)

                html_parts.append('</div>')  # end subcategory

            html_parts.append('</div>')  # end category-section

        return '\n'.join(html_parts)

    def _generate_news_item_html(self, item: NewsItem) -> str:
        """
        生成单个新闻条目的HTML
        """
        time_str = self._format_published(item)
        summary = escape(item.summary) if item.summary else "暂无摘要"
        title = escape(item.title) if item.title else "无标题"
        source = escape(item.source) if item.source else "未知来源"
        has_valid_link = self._is_valid_news_link(item.link)
        link = escape(item.link, quote=True) if has_valid_link else ""
        focus_reason = escape(item.focus_reason) if getattr(item, "focus_reason", "") else ""
        impact_tags = self._extract_signal_tags(item)
        tags_html = "".join(
            f'<span class="tag impact">{escape(tag)}</span>'
            for tag in impact_tags[:3]
        )

        return f'''<div class="news-item">
    <div class="news-title">
        {self._render_title_link(title, link)}
    </div>
    {f'<div class="news-tag-row">{tags_html}</div>' if tags_html else ''}
    {f'<div class="news-focus">{focus_reason}</div>' if focus_reason else ''}
    <div class="news-summary">{summary}</div>
    <div class="news-meta">
        <span class="news-source">{source}</span>
        <span class="news-time">{time_str}</span>
    </div>
</div>'''

    def _is_valid_news_link(self, link: str) -> bool:
        clean_link = (link or "").strip().lower()
        return clean_link.startswith("http://") or clean_link.startswith("https://")

    def _render_title_link(self, title: str, link: str) -> str:
        if link:
            return f'<a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>'
        return f'<span>{title}</span>'

    def _generate_plain_text(self, subject: str, news_items: List[NewsItem]) -> str:
        lines = [subject, ""]
        organized = self._organize_by_category(news_items)
        for category in CATEGORY_DISPLAY_ORDER:
            if category not in organized:
                continue
            lines.append(f"{category}")
            lines.append("-" * len(category))
            subcategories = organized[category]
            ordered_subcategories = SUBCATEGORY_DISPLAY_ORDER.get(category, [])
            sorted_subcategories = sorted(
                subcategories.items(),
                key=lambda pair: (
                    ordered_subcategories.index(pair[0])
                    if pair[0] in ordered_subcategories
                    else len(ordered_subcategories),
                    pair[0],
                )
            )
            for subcategory, items in sorted_subcategories:
                lines.append(f"[{subcategory}]")
                for item in items:
                    lines.append(f"1. {item.title}")
                    if item.summary:
                        lines.append(f"   摘要: {item.summary}")
                    if item.link:
                        lines.append(f"   链接: {item.link}")
                lines.append("")
        return "\n".join(lines).strip()

    def _send_email(self, subject: str, html_content: str, news_items: List[NewsItem]) -> bool:
        """
        发送邮件
        """
        try:
            if not self.recipient_emails:
                logger.error("邮件发送失败: 未配置收件人")
                return False

            logger.info(f"正在发送邮件到 {len(self.recipient_emails)} 个收件人...")

            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            sender_display_name = str(Header(self.sender_name, 'utf-8'))
            msg['From'] = formataddr((sender_display_name, self.sender_email))
            msg['To'] = ', '.join(self.recipient_emails)
            if self.reply_to:
                msg['Reply-To'] = self.reply_to

            text_part = MIMEText(self._generate_plain_text(subject, news_items), 'plain', 'utf-8')
            msg.attach(text_part)

            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # 连接SMTP服务器
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()

            # 登录
            server.login(self.sender_email, self.sender_password)

            # 发送邮件
            server.sendmail(
                self.sender_email,
                self.recipient_emails,
                msg.as_string()
            )

            # 关闭连接
            server.quit()

            logger.info("邮件发送成功!")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}")
            return False


def send_news_email(news_items: List[NewsItem], date: datetime = None) -> bool:
    """
    便捷函数：发送新闻邮件
    """
    sender = EmailSender()
    return sender.send_news_email(news_items, date)


if __name__ == "__main__":
    # 测试邮件发送功能
    from fetcher import fetch_news
    from classifier import classify_news
    from summarizer import generate_summaries

    # 抓取新闻
    news = fetch_news()

    if news:
        # 分类
        news = classify_news(news)

        # 生成摘要
        news = generate_summaries(news)

        # 发送邮件
        sender = EmailSender()
        result = sender.send_news_email(news)

        if result:
            print("邮件发送成功！请检查收件箱。")
        else:
            print("邮件发送失败，请检查配置。")
    else:
        print("没有抓取到新闻，无法发送邮件。")
