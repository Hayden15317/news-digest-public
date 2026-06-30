"""
摘要生成模块 - 负责为新闻生成简短摘要
"""

import logging
import re
from typing import List, Optional
from fetcher import NewsItem
from config import SUMMARY_MAX_LENGTH

logger = logging.getLogger(__name__)


class NewsSummarizer:
    """新闻摘要生成器"""

    def __init__(self):
        self.max_length = SUMMARY_MAX_LENGTH

    def generate_summary(self, news_item: NewsItem) -> str:
        """
        为单条新闻生成摘要
        """
        # 如果已有摘要且长度合适，直接返回
        if news_item.summary and len(news_item.summary) >= 20:
            cleaned_summary = self._clean_text(news_item.summary)
            return self._truncate(cleaned_summary)

        # 尝试从内容中提取摘要
        if news_item.content:
            content_summary = self._extract_from_content(news_item.content)
            if content_summary:
                return content_summary

        # 从标题提取关键信息作为摘要
        title_summary = self._extract_from_title(news_item.title)
        if title_summary:
            return title_summary

        # 如果都没有，返回默认摘要
        return "暂无摘要。"

    def _clean_text(self, text: str) -> str:
        """
        清理文本
        """
        if not text:
            return ""

        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)

        # 移除特殊字符
        text = re.sub(r'[\n\r\t]', ' ', text)

        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)

        # 移除广告和无关内容
        ad_patterns = [
            r'推荐阅读.*',
            r'本文来源.*',
            r'免责声明.*',
            r'版权声明.*',
            r'责任编辑.*',
            r'更多.*资讯.*',
            r'点击.*查看.*',
            r'关注.*公众号.*',
        ]

        for pattern in ad_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        return text.strip()

    def _truncate(self, text: str) -> str:
        """
        截断文本到指定长度
        """
        if not text:
            return ""

        if len(text) <= self.max_length:
            return text

        # 在句子边界截断
        truncated = text[:self.max_length]

        # 尝试在最后一个句号、问号或感叹号处截断
        last_punct = max(
            truncated.rfind('。'),
            truncated.rfind('？'),
            truncated.rfind('！'),
            truncated.rfind('.'),
            truncated.rfind('?'),
            truncated.rfind('!')
        )

        if last_punct > self.max_length * 0.5:  # 确保不会太短
            truncated = truncated[:last_punct + 1]
        else:
            # 如果没有合适的标点，在空格处截断
            last_space = truncated.rfind(' ')
            if last_space > self.max_length * 0.7:
                truncated = truncated[:last_space]
            truncated += "..."

        return truncated.strip()

    def _extract_from_content(self, content: str) -> Optional[str]:
        """
        从正文内容中提取摘要
        """
        if not content:
            return None

        # 清理内容
        cleaned = self._clean_text(content)

        if not cleaned:
            return None

        # 提取前几句作为摘要
        sentences = re.split(r'[。！？.!?]', cleaned)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            return None

        # 取前1-2句
        summary_sentences = sentences[:2]
        summary = '。'.join(summary_sentences)

        if not summary.endswith(('。', '！', '？', '.', '!', '?')):
            summary += '。'

        return self._truncate(summary)

    def _extract_from_title(self, title: str) -> Optional[str]:
        """
        从标题中提取关键信息作为摘要
        """
        if not title:
            return None

        # 清理标题
        cleaned = self._clean_text(title)

        # 如果标题已经很长，直接返回
        if len(cleaned) > 30:
            return self._truncate(cleaned if cleaned.endswith(("。", "！", "？")) else f"{cleaned}。")

        # 否则生成一句简洁摘要，避免邮件里出现无意义的“点击查看详情”文案
        if cleaned.endswith(("。", "！", "？")):
            return cleaned
        return f"{cleaned}。"

    def generate_summaries(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        为所有新闻生成摘要
        """
        logger.info(f"开始为 {len(news_items)} 条新闻生成摘要...")

        for i, item in enumerate(news_items):
            try:
                summary = self.generate_summary(item)
                item.summary = summary

                if (i + 1) % 10 == 0:
                    logger.info(f"已处理 {i + 1}/{len(news_items)} 条新闻")

            except Exception as e:
                logger.error(f"生成摘要时出错: {str(e)}")
                item.summary = "摘要生成失败"

        logger.info("摘要生成完成")
        return news_items


def generate_summaries(news_items: List[NewsItem]) -> List[NewsItem]:
    """
    便捷函数：为新闻生成摘要
    """
    summarizer = NewsSummarizer()
    return summarizer.generate_summaries(news_items)


if __name__ == "__main__":
    # 测试摘要生成功能
    from fetcher import fetch_news

    # 抓取新闻
    news = fetch_news()

    if news:
        # 生成摘要
        summarizer = NewsSummarizer()
        news_with_summary = summarizer.generate_summaries(news)

        # 输出结果
        print("\n摘要生成结果示例:")
        for item in news_with_summary[:5]:
            print(f"\n标题: {item.title}")
            print(f"摘要: {item.summary}")
            print(f"摘要长度: {len(item.summary)} 字符")
            print("-" * 80)
    else:
        print("没有抓取到新闻")
