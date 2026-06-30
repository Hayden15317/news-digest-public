"""
用户偏好过滤模块 - 负责按订阅用户偏好筛选新闻
"""

from datetime import datetime
from typing import List, Tuple

from config import CURRENT_AFFAIRS_KEYWORDS, GFFUNDS_FOCUS_KEYWORDS, GFFUNDS_STRONG_KEYWORDS, POLICY_SIGNAL_KEYWORDS
from fetcher import NewsItem
from user_config import UserProfile

FUND_RELATED_KEYWORDS = (
    "基金", "公募", "私募", "etf", "fof", "reits", "基金ta", "登记结算",
    "清算交收", "份额登记", "基金销售", "销售机构", "代销", "直销", "持有人",
    "基金账户", "中国结算", "中证登", "基金业协会",
)

MACRO_RELATED_KEYWORDS = (
    "宏观", "流动性", "货币政策", "财政政策", "社融", "lpr", "mlf", "逆回购",
    "降准", "降息", "人民币", "汇率", "利率", "国债", "财政", "经济数据",
)


class UserNewsFilter:
    """按用户偏好筛选新闻"""

    def filter_for_user(self, news_items: List[NewsItem], profile: UserProfile) -> List[NewsItem]:
        preferences = profile.preferences
        filtered: List[Tuple[int, int, NewsItem]] = []

        for index, item in enumerate(news_items):
            if not self._matches_profile(item, profile):
                continue

            score = self._score_item(item, profile)
            filtered.append((score, index, item))

        filtered.sort(key=lambda entry: (-entry[0], entry[1]))
        result = [item for _, _, item in filtered]
        return result[: preferences.max_items]

    def _matches_profile(self, item: NewsItem, profile: UserProfile) -> bool:
        preferences = profile.preferences

        if preferences.categories and item.category not in preferences.categories:
            return False

        if preferences.subcategories and item.subcategory not in preferences.subcategories:
            return False

        if item.relevance_score < preferences.min_relevance_score:
            return False

        text = self._build_text(item)

        if preferences.exclude_keywords:
            for keyword in preferences.exclude_keywords:
                if keyword.lower() in text:
                    return False

        if preferences.include_keywords:
            if any(keyword.lower() in text for keyword in preferences.include_keywords):
                return True

            # 行业与金融新闻更适合“基金优先、但不过窄”的软门槛
            if item.category == "行业新闻":
                if item.subcategory in {"基金TA", "基金"}:
                    return True
                if any(keyword in text for keyword in FUND_RELATED_KEYWORDS):
                    return True

            if item.category == "金融新闻":
                if item.subcategory in {"宏观经济", "利率", "汇率", "行情"}:
                    return True
                if any(keyword in text for keyword in MACRO_RELATED_KEYWORDS):
                    return True

            # 时政新闻需要更宽的容错，避免被基金/央行类关键词误伤后只剩极少数条目
            if item.category == "时政新闻":
                if any(keyword.lower() in text for keyword in CURRENT_AFFAIRS_KEYWORDS):
                    return True
                if any(keyword.lower() in text for keyword in POLICY_SIGNAL_KEYWORDS):
                    return True

            return False

        return True

    def _score_item(self, item: NewsItem, profile: UserProfile) -> int:
        preferences = profile.preferences
        score = item.priority_score + item.relevance_score

        if item.category == "行业新闻":
            score += 24
        elif item.category == "金融新闻":
            score += 8
        elif item.category == "时政新闻":
            score += 16

        if item.subcategory == "基金TA":
            score += 28
        elif item.subcategory == "基金":
            score += 24
        elif item.subcategory in {"民生", "社会"}:
            score += 18
        elif item.subcategory in {"宏观经济", "国务院", "发改委", "人大"}:
            score += 12
        elif item.subcategory in {"利率", "汇率", "央行", "财政部"}:
            score += 10
        elif item.subcategory == "证监会":
            score += 3
        elif item.subcategory == "证券":
            score += 4
        elif item.subcategory in {"A股", "港股"}:
            score += 2

        if item.is_domestic:
            score += 10

        text = self._build_text(item)
        for keyword in preferences.include_keywords:
            if keyword.lower() in text:
                score += 8

        title_text = (item.title or "").lower()
        score += sum(5 for keyword in GFFUNDS_FOCUS_KEYWORDS if keyword.lower() in title_text)
        score += sum(7 for keyword in GFFUNDS_STRONG_KEYWORDS if keyword.lower() in title_text)
        score += sum(4 for keyword in POLICY_SIGNAL_KEYWORDS if keyword.lower() in text)
        score += sum(4 for keyword in CURRENT_AFFAIRS_KEYWORDS if keyword.lower() in text)

        if getattr(item, "focus_reason", ""):
            score += 12

        source = item.source or ""
        for name, boost in {
            "基金业协会": 14,
            "中国结算": 14,
            "中证登": 14,
            "东方财富": 7,
            "21财经": 7,
            "券商中国": 4,
            "证券时报": 4,
            "上海证券报": 4,
            "中国证券报": 4,
            "中国政府网": 12,
            "新华网": 12,
            "中国新闻网": 11,
            "央视网": 11,
            "国家发展改革委": 9,
            "全国人大": 9,
            "人民银行": 10,
            "财政部": 10,
            "证监会": 10,
        }.items():
            if name in source:
                score += boost
                break

        hours_old = max(0.0, (datetime.now() - item.published).total_seconds() / 3600)
        score += max(0, 18 - int(hours_old / 2))

        return score

    def _build_text(self, item: NewsItem) -> str:
        return " ".join(
            [
                item.title or "",
                item.summary or "",
                item.content or "",
                item.source or "",
                item.category or "",
                item.subcategory or "",
                getattr(item, "focus_reason", "") or "",
            ]
        ).lower()
