"""
新闻抓取模块 - 优先抓取国内行业新闻，并兼容 RSS / HTML / 公开 JSON 接口
"""

import logging
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

from config import (
    CATEGORY_LIMITS,
    CATEGORY_MINIMUMS,
    CATEGORY_DISPLAY_ORDER,
    CURRENT_AFFAIRS_KEYWORDS,
    DEFAULT_MAX_ITEMS_PER_SOURCE,
    DETAIL_FETCH_BUDGET,
    DOMESTIC_KEYWORDS,
    GFFUNDS_EXCLUDE_KEYWORDS,
    GFFUNDS_FOCUS_KEYWORDS,
    GFFUNDS_STRONG_KEYWORDS,
    INDUSTRY_PRIORITY_KEYWORDS,
    MAX_NEWS_PER_SOURCE,
    MAX_TOTAL_NEWS,
    NEWS_DAYS_LIMIT,
    NEWS_SOURCE_CONFIGS,
    POLICY_SIGNAL_KEYWORDS,
    PREFERRED_SOURCE_MINIMUMS,
    PREFERRED_SUBCATEGORY_LIMITS,
    PREFER_PREVIOUS_DAY_IN_MORNING,
    PREVIOUS_DAY_PRIORITY_BOOST,
    RELEVANCE_SCORE_THRESHOLD,
    REQUEST_DELAY,
    REQUEST_RETRIES,
    REQUEST_TIMEOUT,
    MORNING_DIGEST_CUTOFF_HOUR,
    SAME_DAY_EARLY_NEWS_PENALTY,
    SOURCE_FAMILY_LIMITS,
    SOURCE_LIMITS,
    SUBCATEGORY_DISPLAY_ORDER,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PLACEHOLDER_TITLES = {
    "中国证券投资基金业协会",
    "中国证券登记结算有限责任公司",
    "中国证券登记结算",
    "中国结算",
    "中国人民银行",
    "财政部",
    "中国证监会",
    "国家发展改革委",
    "全国人大",
    "新华网",
    "中国新闻网",
    "央视网",
    "港股通交易结算日历",
    "中国政府网微博、微信",
    "中国政府网微博微信",
    "中国政府网微信",
    "中国政府网微博",
}

NAVIGATION_TITLE_KEYWORDS = (
    "首页", "主页", "更多", "详情", "返回", "上一页", "下一页",
    "通知公告", "协会要闻", "要闻动态", "基金与配置", "栏目导航",
)

PLACEHOLDER_TITLE_FRAGMENTS = (
    "服务专区",
    "业务专区",
    "基金业务服务专区",
    "基金与资产管理业务",
    "直销服务平台",
    "投资者服务专区",
    "基金e账户",
    "基金e账户业务",
    "业务办理",
    "栏目列表",
    "交易结算日历",
    "结算日历",
    "微博、微信",
    "微博微信",
    "政策库",
)

EVENT_TITLE_HINTS = (
    "关于", "发布", "公布", "印发", "实施", "上线", "启动", "开通",
    "调整", "优化", "修订", "答记者问", "解读", "通报", "提示", "提醒",
    "受理", "安排", "公告", "通知", "公示", "征求意见",
)

ENTRY_PAGE_HINTS = (
    "微博",
    "微信",
    "客户端",
    "公众号",
    "小程序",
)

TITLE_NOISE_PATTERNS = (
    r"[“”\"'‘’]",
    r"[·•]",
    r"[，,。.!！?？:：;；、\-—_]",
    r"\s+",
)


@dataclass
class NewsItem:
    """新闻条目数据类"""

    title: str
    link: str
    summary: str
    published: datetime
    source: str
    category: str
    subcategory: str
    content: str = ""
    priority_score: int = 0
    relevance_score: int = 0
    is_domestic: bool = True
    focus_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["published"] = self.published.isoformat()
        return data


class NewsFetcher:
    """新闻抓取器"""

    def __init__(self):
        self.news_items: List[NewsItem] = []
        self.session = requests.Session()
        self.now = datetime.now()
        self.preferred_news_date = self._determine_preferred_news_date(self.now)
        self.detail_metadata_cache: Dict[str, Dict[str, Any]] = {}
        self.remaining_detail_budget = DETAIL_FETCH_BUDGET
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )

    def fetch_all_news(self) -> List[NewsItem]:
        """抓取所有类别的新闻，并优先保留国内行业新闻"""
        logger.info("开始抓取国内优先新闻...")
        self.news_items = []
        self.now = datetime.now()
        self.preferred_news_date = self._determine_preferred_news_date(self.now)
        self.remaining_detail_budget = DETAIL_FETCH_BUDGET

        source_configs = sorted(
            NEWS_SOURCE_CONFIGS,
            key=lambda item: item.get("priority", 0),
            reverse=True,
        )

        for source in source_configs:
            source_started_at = time.monotonic()
            try:
                source_items = self._fetch_from_source(source)
                self.news_items.extend(source_items)
                logger.info(
                    "来源 %s 抓取完成，获得 %s 条新闻，耗时 %.2f 秒",
                    source["name"],
                    len(source_items),
                    time.monotonic() - source_started_at,
                )
            except Exception as exc:
                logger.error(
                    "来源 %s 抓取失败，耗时 %.2f 秒: %s",
                    source["name"],
                    time.monotonic() - source_started_at,
                    exc,
                )

            time.sleep(REQUEST_DELAY)

        self._deduplicate_and_sort()
        self.news_items = self._select_balanced_news(self.news_items)

        if len(self.news_items) > MAX_TOTAL_NEWS:
            self.news_items = self.news_items[:MAX_TOTAL_NEWS]

        logger.info("新闻抓取完成，共 %s 条新闻", len(self.news_items))
        return self.news_items

    def _determine_preferred_news_date(self, now: datetime):
        if PREFER_PREVIOUS_DAY_IN_MORNING and now.hour < MORNING_DIGEST_CUTOFF_HOUR:
            return (now - timedelta(days=1)).date()
        return now.date()

    def _fetch_from_source(self, source: Dict[str, Any]) -> List[NewsItem]:
        source_type = source.get("type", "rss")
        if source_type == "rss":
            return self._fetch_from_rss(source)
        if source_type == "cls_api":
            return self._fetch_from_cls_api(source)
        if source_type == "html_list":
            return self._fetch_from_html_list(source)
        raise ValueError(f"不支持的新闻源类型: {source_type}")

    def _fetch_from_rss(self, source: Dict[str, Any]) -> List[NewsItem]:
        response = self._request(
            source["url"],
            params=source.get("params"),
            headers=source.get("headers"),
        )
        feed = feedparser.parse(response.content)
        source_name = feed.feed.get("title") or source["name"]
        items: List[NewsItem] = []

        for entry in feed.entries[: source.get("limit", MAX_NEWS_PER_SOURCE)]:
            published = self._parse_entry_date(entry)
            news_item = NewsItem(
                title=self._clean_text(entry.get("title", "")),
                link=entry.get("link", ""),
                summary=self._extract_entry_summary(entry),
                published=published,
                source=source_name,
                category=source["category"],
                subcategory=source["subcategory"],
                content=self._extract_entry_summary(entry),
                is_domestic=source.get("domestic", False),
            )
            if self._should_keep_item(news_item, source):
                items.append(news_item)
        return items

    def _fetch_from_cls_api(self, source: Dict[str, Any]) -> List[NewsItem]:
        rows = self._load_cls_rows(source)
        items: List[NewsItem] = []

        for row in rows[: source.get("limit", MAX_NEWS_PER_SOURCE)]:
            content = self._clean_text(row.get("content", ""))
            title = self._clean_text(row.get("title") or self._build_title_from_content(content))
            summary = self._clean_text(row.get("brief") or content)
            published = self._parse_timestamp(row.get("ctime"))
            news_item = NewsItem(
                title=title,
                link=row.get("shareurl") or row.get("url") or source.get("web_url", source["url"]),
                summary=summary,
                published=published,
                source=source["name"],
                category=source["category"],
                subcategory=source["subcategory"],
                content=content,
                is_domestic=True,
            )
            if self._should_keep_item(news_item, source):
                items.append(news_item)
        return items

    def _load_cls_rows(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        primary_error: Optional[Exception] = None

        try:
            response = self._request(
                source["url"],
                params=source.get("params"),
                headers=source.get("headers"),
            )
            payload = response.json()
            rows = payload.get("data", {}).get("roll_data", [])
            if rows:
                return rows
        except Exception as exc:
            primary_error = exc
            logger.warning("财联社主接口不可用，尝试回退接口: %s", exc)

        fallback_url = "https://www.cls.cn/v1/roll/get_roll_list"
        fallback_params = {
            "app": "CailianpressWeb",
            "category": "",
            "os": "web",
            "rn": source.get("params", {}).get("rn", "60"),
        }

        response = self._request(
            fallback_url,
            params=fallback_params,
            headers={"Referer": "https://www.cls.cn/telegraph"},
        )
        payload = response.json()
        rows = payload.get("data", {}).get("roll_data", [])
        if rows:
            return rows

        if primary_error is not None:
            logger.warning("财联社主接口与回退接口均不可用，已自动跳过该来源")
        return []

    def _fetch_from_html_list(self, source: Dict[str, Any]) -> List[NewsItem]:
        response = self._request(
            source["url"],
            params=source.get("params"),
            headers=source.get("headers"),
        )
        soup = BeautifulSoup(response.text, "html.parser")

        anchors = []
        for selector in source.get("link_selectors", []):
            anchors.extend(soup.select(selector))
        if not anchors:
            anchors = soup.select("a[href]")

        items: List[NewsItem] = []
        seen = set()
        detail_budget_for_source = int(source.get("detail_budget", 3) or 0)
        detail_fetch_count = 0

        for anchor in anchors:
            href = (anchor.get("href") or "").strip()
            title = self._clean_text(anchor.get_text(" ", strip=True))

            if not href or not title or len(title) < 8:
                continue
            if self._should_ignore_link(href, source):
                continue
            if self._is_placeholder_title(title, source):
                continue

            full_link = urljoin(source.get("base_url", source["url"]), href)
            dedupe_key = self._normalize_key(full_link or title)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            published, detail_used_for_time = self._extract_html_list_datetime(anchor, source, detail_fetch_count, detail_budget_for_source)
            if detail_used_for_time:
                detail_fetch_count += 1
            summary = ""
            allow_detail_fetch = self._can_fetch_detail(detail_fetch_count, detail_budget_for_source)
            if allow_detail_fetch and (source.get("resolve_detail_fields") or self._should_enrich_title(title)):
                detail_data = self._resolve_detail_metadata(full_link)
                detail_fetch_count += 1
                title = detail_data.get("title") or title
                summary = detail_data.get("summary") or summary
                if detail_data.get("published"):
                    published = detail_data["published"]
                if self._is_placeholder_title(title, source):
                    continue
            news_item = NewsItem(
                title=title,
                link=full_link,
                summary=summary,
                published=published or datetime.now(),
                source=source["name"],
                category=source["category"],
                subcategory=source["subcategory"],
                content="",
                is_domestic=source.get("domestic", False),
            )
            if self._should_keep_item(news_item, source):
                items.append(news_item)
            if len(items) >= source.get("limit", MAX_NEWS_PER_SOURCE):
                break

        return items

    def _extract_html_list_datetime(
        self,
        anchor: Any,
        source: Dict[str, Any],
        detail_fetch_count: int,
        detail_budget_for_source: int,
    ) -> tuple[Optional[datetime], bool]:
        candidate_texts = self._collect_nearby_datetime_candidates(anchor)
        list_published = self._select_best_datetime_from_texts(candidate_texts)
        if list_published:
            return list_published, False

        if source.get("resolve_detail_time", False):
            href = (anchor.get("href") or "").strip()
            if href and self._can_fetch_detail(detail_fetch_count, detail_budget_for_source):
                full_link = urljoin(source.get("base_url", source["url"]), href)
                detail_data = self._resolve_detail_metadata(full_link)
                return detail_data.get("published"), True

        return None, False

    def _collect_nearby_datetime_candidates(self, anchor: Any) -> List[str]:
        candidates: List[str] = []
        nearby_tags: List[Any] = [anchor]

        parent = getattr(anchor, "parent", None)
        if parent is not None:
            nearby_tags.append(parent)
            grandparent = getattr(parent, "parent", None)
            if grandparent is not None:
                nearby_tags.append(grandparent)

        for tag in nearby_tags:
            candidates.extend(self._extract_datetime_attribute_candidates(tag))
            try:
                text = self._clean_text(tag.get_text(" ", strip=True))
            except Exception:
                text = ""
            if text and len(text) <= 120:
                candidates.append(text)

            try:
                sibling_tags = list(getattr(tag, "children", []))
            except Exception:
                sibling_tags = []

            for child in sibling_tags[:8]:
                if getattr(child, "name", None) is None:
                    child_text = self._clean_text(str(child))
                    if child_text and len(child_text) <= 80:
                        candidates.append(child_text)
                    continue

                candidates.extend(self._extract_datetime_attribute_candidates(child))
                child_text = self._clean_text(child.get_text(" ", strip=True))
                if child_text and len(child_text) <= 80:
                    candidates.append(child_text)

        return candidates

    def _extract_datetime_attribute_candidates(self, tag: Any) -> List[str]:
        if not getattr(tag, "attrs", None):
            return []

        candidates: List[str] = []
        attr_names = (
            "datetime",
            "title",
            "content",
            "data-time",
            "data-date",
            "data-datetime",
            "data-pubtime",
            "data-publish-time",
            "data-published",
            "data-created-at",
            "data-updated-at",
        )
        for attr_name in attr_names:
            value = tag.attrs.get(attr_name)
            if isinstance(value, str) and value.strip():
                candidates.append(value.strip())
        return candidates

    def _resolve_detail_metadata(self, link: str) -> Dict[str, Any]:
        if link in self.detail_metadata_cache:
            return self.detail_metadata_cache[link]

        result: Dict[str, Any] = {"title": "", "summary": "", "published": None}
        if self.remaining_detail_budget <= 0:
            self.detail_metadata_cache[link] = result
            return result

        try:
            self.remaining_detail_budget -= 1
            response = self._request(link)
            soup = BeautifulSoup(response.text, "html.parser")

            result["title"] = self._extract_detail_title(soup)
            result["summary"] = self._extract_detail_summary(soup)
            result["published"] = self._extract_detail_published(soup)
        except Exception:
            pass

        self.detail_metadata_cache[link] = result
        return result

    def _can_fetch_detail(self, detail_fetch_count: int, detail_budget_for_source: int) -> bool:
        if detail_budget_for_source <= 0:
            return False
        if detail_fetch_count >= detail_budget_for_source:
            return False
        return self.remaining_detail_budget > 0

    def _get_meta_content(self, soup: BeautifulSoup, target_keys: List[str]) -> List[str]:
        matched: List[str] = []
        target_set = {key.lower() for key in target_keys}
        for node in soup.select("meta"):
            for attr_name in ("name", "property", "itemprop", "http-equiv"):
                attr_value = (node.get(attr_name) or "").strip().lower()
                if attr_value and attr_value in target_set:
                    content = (node.get("content") or "").strip()
                    if content:
                        matched.append(content)
        return matched

    def _extract_detail_title(self, soup: BeautifulSoup) -> str:
        for content in self._get_meta_content(soup, ["og:title", "title", "ArticleTitle"]):
            title = self._clean_title(content)
            if title and len(title) >= 6:
                return title

        selectors = [
            "h1",
            ".article-title",
            ".title",
            "title",
        ]
        for selector in selectors:
            node = soup.select_one(selector)
            if not node:
                continue
            title = (node.get("content") or node.get_text(" ", strip=True)).strip()
            title = self._clean_title(title)
            if title and len(title) >= 6:
                return title
        return ""

    def _extract_detail_summary(self, soup: BeautifulSoup) -> str:
        for content in self._get_meta_content(soup, ["description", "og:description", "Description"]):
            summary = self._clean_text(content)
            if 20 <= len(summary) <= 220:
                return summary

        selectors = [
            ".summary",
            ".article-summary",
            ".desc",
            "p",
        ]
        for selector in selectors:
            nodes = soup.select(selector)
            for node in nodes[:5]:
                summary = (node.get("content") or node.get_text(" ", strip=True)).strip()
                summary = self._clean_text(summary)
                if 20 <= len(summary) <= 220:
                    return summary
        return ""

    def _extract_detail_published(self, soup: BeautifulSoup) -> Optional[datetime]:
        candidates: List[str] = []
        candidates.extend(
            self._get_meta_content(
                soup,
                [
                    "article:published_time",
                    "og:release_date",
                    "pubdate",
                    "PubDate",
                    "publishdate",
                    "publish-date",
                    "article:published_time",
                    "datePublished",
                ],
            )
        )

        raw_html = str(soup)
        raw_patterns = [
            r"(?:发布时间|发布于|更新时间|时间)[^0-9]{0,30}(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)",
            r"(?:发布时间|发布于|更新时间|时间)[^0-9]{0,30}(\d{4}年\d{1,2}月\d{1,2}日\s+\d{1,2}:\d{2}(?::\d{2})?)",
            r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)",
            r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}(?::\d{2})?)",
            r"(\d{4}年\d{1,2}月\d{1,2}日\s+\d{1,2}:\d{2}(?::\d{2})?)",
        ]
        for pattern in raw_patterns:
            candidates.extend(re.findall(pattern, raw_html, re.IGNORECASE))

        for node in soup.select("time, span, div, p")[:80]:
            candidates.extend(self._extract_datetime_attribute_candidates(node))
            text = self._clean_text(node.get_text(" ", strip=True))
            if text and len(text) <= 120:
                candidates.append(text)

        return self._select_best_datetime_from_texts(candidates)

    def _select_best_datetime_from_texts(self, candidate_texts: List[str]) -> Optional[datetime]:
        best_match: Optional[datetime] = None
        best_score = -10**9

        for text in candidate_texts:
            parsed = self._parse_datetime_text(text)
            if not parsed:
                continue
            score = self._score_datetime_candidate(text, parsed)
            if score > best_score:
                best_score = score
                best_match = parsed

        return best_match

    def _score_datetime_candidate(self, text: str, parsed: datetime) -> int:
        score = 0
        cleaned = self._clean_text(text).lower()
        has_time = self._text_has_explicit_time(cleaned)

        if has_time:
            score += 100
        else:
            score += 10

        if any(keyword in cleaned for keyword in ("发布时间", "发布于", "publish", "pubdate", "datepublished", "更新时间", "更新于", "时间")):
            score += 30

        if len(cleaned) <= 40:
            score += 15
        elif len(cleaned) <= 80:
            score += 5
        else:
            score -= 10

        if parsed.hour == 0 and parsed.minute == 0 and not has_time:
            score -= 25

        # 没有显式时分、且时间非常接近抓取时刻时，通常是错误命中或默认值
        if not has_time and abs((self.now - parsed).total_seconds()) < 600:
            score -= 40

        return score

    def _text_has_explicit_time(self, text: str) -> bool:
        time_patterns = [
            r"\d{1,2}:\d{2}(:\d{2})?",
            r"t\d{2}:\d{2}",
            r"昨天\s*\d{1,2}:\d{2}",
            r"前天\s*\d{1,2}:\d{2}",
            r"\d+\s*小时前",
            r"\d+\s*分钟前",
            r"刚刚",
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in time_patterns)

    def _clean_title(self, title: str) -> str:
        if not title:
            return ""
        title = self._clean_text(title)
        separators = ["_ ", "_", " - ", "|", "—"]
        for separator in separators:
            if separator in title:
                title = title.split(separator)[0].strip()
        return title

    def _should_enrich_title(self, title: str) -> bool:
        if not title:
            return True
        if len(title) > 60:
            return True
        punctuation_hits = sum(title.count(mark) for mark in ("。", "；", "："))
        return punctuation_hits >= 2

    def _request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        merged_headers = dict(self.session.headers)
        if headers:
            merged_headers.update(headers)

        last_error: Optional[Exception] = None
        for _ in range(REQUEST_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=merged_headers,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                response.encoding = self._resolve_response_encoding(response)
                return response
            except Exception as exc:
                last_error = exc
                time.sleep(REQUEST_DELAY)

        raise RuntimeError(f"请求失败: {url}") from last_error

    def _resolve_response_encoding(self, response: requests.Response) -> str:
        """
        统一修正网页编码，避免中文页面被错误地按 ISO-8859-1 解码后出现乱码。
        """
        encoding = (response.encoding or "").lower()
        apparent = (response.apparent_encoding or "").lower()

        if not encoding:
            return apparent or "utf-8"

        # 很多国内站点未声明 charset，requests 会默认给出 ISO-8859-1，需强制纠正。
        if encoding == "iso-8859-1":
            if apparent.startswith(("utf", "gb", "gbk", "gb2312", "gb18030")):
                return apparent
            return "utf-8"

        return response.encoding

    def _should_keep_item(self, news_item: NewsItem, source: Dict[str, Any]) -> bool:
        if not news_item.title:
            return False

        if self._is_placeholder_title(news_item.title, source):
            return False

        source_days_limit = int(source.get("days_limit", NEWS_DAYS_LIMIT) or 0)
        if source_days_limit > 0:
            cutoff = self.now - timedelta(days=source_days_limit)
            if news_item.published < cutoff:
                return False

        text = f"{news_item.title} {news_item.summary} {news_item.content}"
        keywords = source.get("keywords", [])
        strict_keywords = source.get("strict_keywords", True)
        if (
            strict_keywords
            and keywords
            and not any(keyword.lower() in text.lower() for keyword in keywords)
        ):
            return False

        if source.get("domestic", False):
            news_item.is_domestic = True
        else:
            news_item.is_domestic = self._looks_domestic(text)

        news_item.relevance_score = self._calculate_relevance_score(news_item)
        news_item.focus_reason = self._build_focus_reason(news_item)
        if not self._passes_relevance_gate(news_item):
            return False

        news_item.priority_score = self._calculate_priority(news_item, source)
        news_item.summary = self._clean_text(news_item.summary)
        news_item.content = self._clean_text(news_item.content)
        return True

    def _calculate_priority(self, news_item: NewsItem, source: Dict[str, Any]) -> int:
        score = int(source.get("priority", 0))
        text = f"{news_item.title} {news_item.summary} {news_item.content}"

        if news_item.category == "行业新闻":
            score += 80
        elif news_item.category == "金融新闻":
            score += 35
        elif news_item.category == "时政新闻":
            score += 25

        if news_item.subcategory in {"基金TA", "基金", "民生", "社会"}:
            score += 30

        if news_item.is_domestic:
            score += 40

        score += sum(6 for keyword in INDUSTRY_PRIORITY_KEYWORDS if keyword in text)
        score += sum(3 for keyword in DOMESTIC_KEYWORDS if keyword in text)
        score += sum(8 for keyword in GFFUNDS_FOCUS_KEYWORDS if keyword in text)
        score += sum(10 for keyword in GFFUNDS_STRONG_KEYWORDS if keyword in text)
        score += sum(5 for keyword in CURRENT_AFFAIRS_KEYWORDS if keyword in text)
        score += news_item.relevance_score * 4

        if news_item.subcategory == "基金TA":
            score += 38
        elif news_item.subcategory == "基金":
            score += 28
        elif news_item.subcategory in {"民生", "社会"}:
            score += 24
        elif news_item.subcategory in {"宏观经济", "国务院", "发改委", "人大"}:
            score += 14
        elif news_item.subcategory in {"利率", "汇率", "央行", "财政部"}:
            score += 10
        elif news_item.subcategory == "证监会":
            score += 4
        elif news_item.subcategory == "证券":
            score += 3
        elif news_item.subcategory in {"A股", "港股"}:
            score += 2

        published_date = news_item.published.date()
        if published_date == self.preferred_news_date:
            score += PREVIOUS_DAY_PRIORITY_BOOST
        elif (
            PREFER_PREVIOUS_DAY_IN_MORNING
            and self.now.hour < MORNING_DIGEST_CUTOFF_HOUR
            and published_date == self.now.date()
        ):
            score -= SAME_DAY_EARLY_NEWS_PENALTY

        hours_old = max(0.0, (self.now - news_item.published).total_seconds() / 3600)
        freshness_bonus = max(0, int(24 - hours_old))
        score += min(24, freshness_bonus)

        return score

    def _calculate_relevance_score(self, news_item: NewsItem) -> int:
        text = f"{news_item.title} {news_item.summary} {news_item.content}"
        score = 0

        if any(keyword in text for keyword in GFFUNDS_EXCLUDE_KEYWORDS):
            return 0

        score += sum(4 for keyword in GFFUNDS_FOCUS_KEYWORDS if keyword in text)
        score += sum(7 for keyword in GFFUNDS_STRONG_KEYWORDS if keyword in text)
        score += sum(3 for keyword in INDUSTRY_PRIORITY_KEYWORDS if keyword in text)
        score += sum(2 for keyword in POLICY_SIGNAL_KEYWORDS if keyword in text)
        score += sum(3 for keyword in CURRENT_AFFAIRS_KEYWORDS if keyword in text)

        if news_item.category == "行业新闻":
            score += 8
        elif news_item.category == "金融新闻":
            score += 4
        elif news_item.category == "时政新闻":
            score += 3

        if news_item.subcategory == "基金TA":
            score += 14
        elif news_item.subcategory == "基金":
            score += 12
        elif news_item.subcategory in {"民生", "社会"}:
            score += 10
        elif news_item.subcategory in {"宏观经济", "国务院", "发改委", "人大"}:
            score += 6
        elif news_item.subcategory in {"利率", "汇率", "央行", "财政部"}:
            score += 5
        elif news_item.subcategory == "证监会":
            score += 2
        elif news_item.subcategory == "证券":
            score += 2
        elif news_item.subcategory in {"A股", "港股"}:
            score += 1

        if news_item.is_domestic:
            score += 5

        return score

    def _passes_relevance_gate(self, news_item: NewsItem) -> bool:
        threshold = RELEVANCE_SCORE_THRESHOLD.get(news_item.category, 99)
        if news_item.relevance_score >= threshold:
            return True

        text = f"{news_item.title} {news_item.summary} {news_item.content}"
        if any(keyword in text for keyword in POLICY_SIGNAL_KEYWORDS):
            return news_item.relevance_score >= max(6, threshold - 2)
        if news_item.category == "时政新闻":
            trusted_sources = ("中国政府网", "新华网", "中国新闻网", "央视网", "国家发展改革委", "全国人大")
            if any(name in (news_item.source or "") for name in trusted_sources):
                return news_item.relevance_score >= max(3, threshold)
            if any(keyword in text for keyword in CURRENT_AFFAIRS_KEYWORDS):
                return news_item.relevance_score >= max(3, threshold)

        return False

    def _build_focus_reason(self, news_item: NewsItem) -> str:
        text = f"{news_item.title} {news_item.summary} {news_item.content}"
        reasons = []

        if any(keyword in text for keyword in ("基金TA", "份额登记", "登记结算", "清算交收", "基金销售", "销售机构", "直销", "代销", "过户", "开户", "账户")):
            reasons.append("关注基金TA、账户登记与销售运营链路")
        if any(keyword in text for keyword in ("基金发行", "新发基金", "ETF", "REITs", "QDII", "指数基金", "FOF")):
            reasons.append("关注基金产品供给与发行节奏")
        if any(keyword in text for keyword in ("公募基金", "基金经理", "持仓", "仓位", "申购", "赎回", "机构资金")):
            reasons.append("关注机构资金与配置方向")
        if any(keyword in text for keyword in ("券商", "证券公司", "IPO", "并购重组", "资本市场", "再融资", "交易所")):
            reasons.append("补充资本市场动态")
        if any(keyword in text for keyword in ("A股", "沪指", "深成指", "融资余额", "北向资金", "风险偏好")):
            reasons.append("关注A股风险偏好与板块风格")
        if any(keyword in text for keyword in ("港股", "港股通", "南向资金", "恒生科技", "恒生指数")):
            reasons.append("关注港股流动性与跨境配置")
        if any(keyword in text for keyword in ("中国人民银行", "LPR", "MLF", "降准", "降息", "社融", "逆回购")):
            reasons.append("关注货币政策与利率预期")
        if any(keyword in text for keyword in ("财政部", "国债", "专项债", "预算", "税收", "赤字")):
            reasons.append("关注财政政策与稳增长线索")
        if any(keyword in text for keyword in ("国务院", "国务院办公厅", "实施意见", "决定", "通知", "国家发展改革委", "全国人大", "法律草案", "修订", "审议")):
            reasons.append("关注时政与部委政策面最新变化")
        if any(keyword in text for keyword in CURRENT_AFFAIRS_KEYWORDS):
            reasons.append("关注最近民生与社会热点")
        if any(keyword in text for keyword in ("医保", "药品", "校园", "公共服务", "城市更新", "食品安全", "反诈", "诈骗", "消防")):
            reasons.append("关注公共服务与社会治理动态")
        if any(keyword in text for keyword in ("人民币", "汇率", "美元指数", "中间价", "离岸人民币")):
            reasons.append("关注汇率波动与外资配置")

        return " / ".join(reasons[:2])

    def _deduplicate_and_sort(self):
        unique_items: List[NewsItem] = []
        seen = set()

        for item in sorted(
            self.news_items,
            key=lambda news: (news.priority_score, news.published),
            reverse=True,
        ):
            key = self._build_dedupe_key(item)
            if not key:
                continue
            if key in seen:
                continue
            seen.add(key)
            unique_items.append(item)

        unique_items.sort(
            key=lambda news: (news.priority_score, news.published),
            reverse=True,
        )
        self.news_items = unique_items

    def _select_balanced_news(self, items: List[NewsItem]) -> List[NewsItem]:
        buckets: Dict[str, List[NewsItem]] = {}
        for item in items:
            buckets.setdefault(item.category, []).append(item)

        selected: List[NewsItem] = []
        selected_keys = set()
        source_counts: Dict[str, int] = {}
        source_family_counts: Dict[str, int] = {}

        def try_add(item: NewsItem) -> bool:
            item_key = self._build_dedupe_key(item)
            if item_key in selected_keys:
                return False
            max_allowed = SOURCE_LIMITS.get(item.source, DEFAULT_MAX_ITEMS_PER_SOURCE)
            if source_counts.get(item.source, 0) >= max_allowed:
                return False
            source_family = self._get_source_family(item.source)
            family_limit = SOURCE_FAMILY_LIMITS.get(source_family)
            if family_limit is not None and source_family_counts.get(source_family, 0) >= family_limit:
                return False
            selected.append(item)
            selected_keys.add(item_key)
            source_counts[item.source] = source_counts.get(item.source, 0) + 1
            source_family_counts[source_family] = source_family_counts.get(source_family, 0) + 1
            return True

        for source_name, limit in PREFERRED_SOURCE_MINIMUMS.items():
            matched = [item for item in items if item.source == source_name]
            for item in matched[:limit]:
                try_add(item)

        # 先按关注子类拿一轮，确保基金主线与民生时政优先进入邮件
        for subcategory, limit in PREFERRED_SUBCATEGORY_LIMITS.items():
            matched = [item for item in items if item.subcategory == subcategory]
            for item in matched[:limit]:
                try_add(item)

        for category in CATEGORY_DISPLAY_ORDER:
            minimum = CATEGORY_MINIMUMS.get(category, 0)
            if minimum <= 0:
                continue
            already = len([item for item in selected if item.category == category])
            if already >= minimum:
                continue
            ordered_subcategories = SUBCATEGORY_DISPLAY_ORDER.get(category, [])
            preferred_items = sorted(
                buckets.get(category, []),
                key=lambda item: (
                    ordered_subcategories.index(item.subcategory)
                    if item.subcategory in ordered_subcategories
                    else len(ordered_subcategories),
                    -item.priority_score,
                    -item.relevance_score,
                ),
            )
            for item in preferred_items:
                if try_add(item):
                    already += 1
                if already >= minimum:
                    break

        for category in CATEGORY_DISPLAY_ORDER:
            category_items = buckets.get(category, [])
            category_count = len([item for item in selected if item.category == category])
            remaining = max(0, CATEGORY_LIMITS.get(category, 0) - category_count)
            if remaining <= 0:
                continue
            for item in category_items:
                if try_add(item):
                    remaining -= 1
                if remaining <= 0:
                    break

        if len(selected) < MAX_TOTAL_NEWS:
            for item in items:
                if not try_add(item):
                    continue
                if len(selected) >= MAX_TOTAL_NEWS:
                    break

        selected.sort(key=lambda news: (news.priority_score, news.published), reverse=True)
        return selected

    def _get_source_family(self, source_name: str) -> str:
        normalized = self._clean_text(source_name)
        if not normalized:
            return "未知来源"
        for separator in ("-", "－", "_", "—", "–"):
            if separator in normalized:
                family = normalized.split(separator, 1)[0].strip()
                if family:
                    return family
        return normalized

    def _parse_entry_date(self, entry: Any) -> datetime:
        for field in ("published_parsed", "updated_parsed", "created_parsed"):
            struct_time = getattr(entry, field, None)
            if struct_time:
                return datetime(*struct_time[:6])
        return datetime.now()

    def _parse_timestamp(self, value: Any) -> datetime:
        try:
            if value is None:
                return datetime.now()
            return datetime.fromtimestamp(int(value))
        except Exception:
            return datetime.now()

    def _parse_datetime_text(self, text: str) -> Optional[datetime]:
        if not text:
            return None

        text = self._clean_text(text)
        if not text:
            return None

        relative_patterns = [
            (r"昨天\s*(\d{1,2}:\d{2})", 1),
            (r"前天\s*(\d{1,2}:\d{2})", 2),
        ]
        for pattern, days_back in relative_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    base_date = (self.now - timedelta(days=days_back)).date()
                    hour, minute = map(int, match.group(1).split(":"))
                    return datetime.combine(base_date, datetime.min.time()).replace(
                        hour=hour,
                        minute=minute,
                    )
                except ValueError:
                    continue

        match = re.search(r"(\d+)\s*小时前", text)
        if match:
            return self.now - timedelta(hours=int(match.group(1)))

        match = re.search(r"(\d+)\s*分钟前", text)
        if match:
            return self.now - timedelta(minutes=int(match.group(1)))

        if "刚刚" in text:
            return self.now

        patterns = [
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})",
            r"(\d{4}年\d{1,2}月\d{1,2}日\s+\d{1,2}:\d{2}:\d{2})",
            r"(\d{4}年\d{1,2}月\d{1,2}日\s+\d{1,2}:\d{2})",
            r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})",
            r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})",
            r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})",
            r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})",
            r"(\d{4}-\d{2}-\d{2})",
            r"(\d{4}/\d{2}/\d{2})",
            r"(\d{4}年\d{1,2}月\d{1,2}日)",
            r"(\d{2}-\d{2}\s+\d{2}:\d{2})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            date_text = match.group(1)
            for fmt in (
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M",
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y年%m月%d日 %H:%M:%S",
                "%Y年%m月%d日 %H:%M",
                "%Y年%m月%d日",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y/%m/%d %H:%M:%S",
                "%Y/%m/%d %H:%M",
            ):
                try:
                    return datetime.strptime(date_text, fmt)
                except ValueError:
                    continue
            if re.fullmatch(r"\d{2}-\d{2}\s+\d{2}:\d{2}", date_text):
                try:
                    parsed = datetime.strptime(f"{self.now.year}-{date_text}", "%Y-%m-%d %H:%M")
                    if parsed - self.now > timedelta(days=1):
                        parsed = parsed.replace(year=parsed.year - 1)
                    return parsed
                except ValueError:
                    continue
        return None

    def _extract_entry_summary(self, entry: Any) -> str:
        for field in ("summary", "description"):
            value = entry.get(field, "")
            if value:
                return self._clean_text(BeautifulSoup(value, "html.parser").get_text(" ", strip=True))
        return ""

    def _should_ignore_link(self, href: str, source: Dict[str, Any]) -> bool:
        link_patterns = source.get("link_patterns", [])
        if link_patterns and not any(pattern in href for pattern in link_patterns):
            return True
        if href.startswith("javascript:") or href.startswith("#"):
            return True
        return False

    def _is_placeholder_title(self, title: str, source: Dict[str, Any]) -> bool:
        clean_title = self._clean_text(title)
        source_name = str(source.get("name", ""))
        if not clean_title:
            return True

        if clean_title in PLACEHOLDER_TITLES:
            return True

        if clean_title in {
            source.get("name", ""),
            source.get("category", ""),
            source.get("subcategory", ""),
        }:
            return True

        source_fragments = [part.strip() for part in str(source.get("name", "")).split("-") if part.strip()]
        if clean_title in source_fragments:
            return True

        if any(keyword == clean_title or keyword in clean_title for keyword in NAVIGATION_TITLE_KEYWORDS):
            if len(clean_title) <= 16:
                return True

        if any(fragment in clean_title for fragment in PLACEHOLDER_TITLE_FRAGMENTS):
            if not any(hint in clean_title for hint in EVENT_TITLE_HINTS):
                return True

        if len(clean_title) <= 20 and clean_title.endswith("日历"):
            return True

        if any(hint in clean_title for hint in ENTRY_PAGE_HINTS):
            if not any(event_hint in clean_title for event_hint in EVENT_TITLE_HINTS):
                if len(clean_title) <= 20 or source_name.startswith("中国政府网"):
                    return True

        if len(clean_title) <= 16 and clean_title.endswith(("协会", "公司", "网站", "网页")):
            return True

        if source_name.startswith(("中国结算", "基金业协会")):
            if len(clean_title) <= 18 and not any(hint in clean_title for hint in EVENT_TITLE_HINTS):
                if any(token in clean_title for token in ("业务", "专区", "服务", "平台", "账户")):
                    return True

        if source_name.startswith("中国结算") and "日历" in clean_title:
            return True

        if source_name.startswith("中国政府网"):
            if any(token in clean_title for token in ("微博", "微信", "客户端", "政策库")):
                if not any(hint in clean_title for hint in EVENT_TITLE_HINTS):
                    return True

        return False

    def _looks_domestic(self, text: str) -> bool:
        return any(keyword in text for keyword in DOMESTIC_KEYWORDS)

    def _build_title_from_content(self, content: str) -> str:
        if not content:
            return "暂无标题"
        stripped = self._clean_text(content)
        if len(stripped) <= 36:
            return stripped
        return stripped[:36] + "..."

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[\r\n\t]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip(" -|")

    def _normalize_key(self, text: str) -> str:
        return re.sub(r"\s+", "", text or "").lower()

    def _build_dedupe_key(self, item: NewsItem) -> str:
        title_key = self._normalize_title_key(item.title)
        link_key = self._normalize_link_key(item.link)
        return title_key or link_key

    def _normalize_title_key(self, title: str) -> str:
        text = self._clean_text(title).lower()
        if not text:
            return ""
        for pattern in TITLE_NOISE_PATTERNS:
            text = re.sub(pattern, "", text)
        return text

    def _normalize_link_key(self, link: str) -> str:
        clean_link = (link or "").strip().lower()
        if not clean_link:
            return ""
        if not clean_link.startswith(("http://", "https://")):
            return ""
        clean_link = clean_link.rstrip("/")
        clean_link = re.sub(r"#.*$", "", clean_link)
        return clean_link


def fetch_news() -> List[NewsItem]:
    """
    便捷函数：抓取新闻
    """
    fetcher = NewsFetcher()
    return fetcher.fetch_all_news()


if __name__ == "__main__":
    # 测试抓取功能
    news = fetch_news()
    print(f"共抓取到 {len(news)} 条新闻\n")

    for item in news[:5]:
        print(f"标题: {item.title}")
        print(f"分类: {item.category} - {item.subcategory}")
        print(f"时间: {item.published}")
        print(f"链接: {item.link}")
        print(f"摘要: {item.summary[:100]}...")
        print("-" * 80)
