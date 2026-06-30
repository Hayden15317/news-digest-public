"""
用户配置模块 - 负责加载多用户收件与偏好配置
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import time
from typing import Any, Dict, List, Optional

from config import (
    CATEGORY_DISPLAY_ORDER,
    RECIPIENT_EMAILS,
    SCHEDULE_TIME,
    SENDER_NAME,
    SUBCATEGORY_DISPLAY_ORDER,
    TIMEZONE,
)

logger = logging.getLogger(__name__)

DEFAULT_USER_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "users.json")
DEFAULT_USER_EXAMPLE_PATH = os.path.join(os.path.dirname(__file__), "users.example.json")


def _normalize_email_list(values: List[str]) -> List[str]:
    emails = []
    for value in values:
        email = (value or "").strip()
        if email:
            emails.append(email)
    return emails


def _parse_time(value: Any, fallback: time) -> time:
    if isinstance(value, time):
        return value
    if not value:
        return fallback
    if not isinstance(value, str):
        return fallback

    parts = value.strip().split(":")
    if len(parts) != 2:
        logger.warning("无法解析发送时间 %r，使用默认时间 %s", value, fallback)
        return fallback

    try:
        hour = int(parts[0])
        minute = int(parts[1])
        return time(hour=hour, minute=minute)
    except ValueError:
        logger.warning("无法解析发送时间 %r，使用默认时间 %s", value, fallback)
        return fallback


def _parse_optional_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_optional_bool(value: Any) -> Optional[bool]:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    return None


def _default_subcategories() -> List[str]:
    result: List[str] = []
    for items in SUBCATEGORY_DISPLAY_ORDER.values():
        result.extend(items)
    return result


def _upgrade_subcategories(subcategories: List[str], categories: List[str]) -> List[str]:
    upgraded = [str(item).strip() for item in subcategories if str(item).strip()]

    def ensure(value: str) -> None:
        if value not in upgraded:
            upgraded.append(value)

    if "行业新闻" in categories:
        if "基金" in upgraded or "证券" in upgraded:
            ensure("基金TA")
    if "时政新闻" in categories:
        ensure("国务院")
        ensure("发改委")
        ensure("民生")
        ensure("社会")

    return upgraded


def _upgrade_include_keywords(include_keywords: List[str], categories: List[str]) -> List[str]:
    upgraded = [str(item).strip() for item in include_keywords if str(item).strip()]

    def ensure(value: str) -> None:
        if value not in upgraded:
            upgraded.append(value)

    if "行业新闻" in categories:
        fund_specific_keywords = {"基金TA", "登记结算", "清算交收", "基金销售", "中国结算", "基金业协会"}
        if not any(keyword in upgraded for keyword in fund_specific_keywords):
            upgraded = [keyword for keyword in upgraded if keyword not in {"券商", "A股", "港股"}]
            ensure("基金TA")
            ensure("登记结算")
            ensure("基金销售")
            ensure("中国结算")

    if "时政新闻" in categories:
        current_affairs_keywords = {"民生", "社会", "高温", "医疗", "教育", "出行"}
        if not any(keyword in upgraded for keyword in current_affairs_keywords):
            ensure("民生")
            ensure("社会")
            ensure("高温")
            ensure("医疗")

    return upgraded


@dataclass
class UserPreferences:
    """单个用户的新闻偏好配置"""

    categories: List[str] = field(default_factory=lambda: list(CATEGORY_DISPLAY_ORDER))
    subcategories: List[str] = field(default_factory=_default_subcategories)
    include_keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)
    max_items: int = 20
    min_relevance_score: int = 0
    send_empty_email: bool = False

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "UserPreferences":
        payload = data or {}
        categories = payload.get("categories") or list(CATEGORY_DISPLAY_ORDER)
        subcategories = payload.get("subcategories") or _default_subcategories()
        include_keywords = [str(item).strip() for item in payload.get("include_keywords", []) if str(item).strip()]
        exclude_keywords = [str(item).strip() for item in payload.get("exclude_keywords", []) if str(item).strip()]

        max_items = payload.get("max_items", 20)
        min_relevance_score = payload.get("min_relevance_score", 0)
        send_empty_email = bool(payload.get("send_empty_email", False))

        try:
            max_items = int(max_items)
        except (TypeError, ValueError):
            max_items = 20

        try:
            min_relevance_score = int(min_relevance_score)
        except (TypeError, ValueError):
            min_relevance_score = 0

        return cls(
            categories=[str(item).strip() for item in categories if str(item).strip()],
            subcategories=_upgrade_subcategories(subcategories, categories),
            include_keywords=_upgrade_include_keywords(include_keywords, categories),
            exclude_keywords=exclude_keywords,
            max_items=max(1, max_items),
            min_relevance_score=min_relevance_score,
            send_empty_email=send_empty_email,
        )


@dataclass
class UserProfile:
    """单个订阅用户配置"""

    user_id: str
    name: str
    recipient_emails: List[str]
    enabled: bool = True
    smtp_server: str = ""
    smtp_port: Optional[int] = None
    smtp_use_ssl: Optional[bool] = None
    sender_email: str = ""
    sender_password: str = ""
    sender_name: str = SENDER_NAME
    reply_to: str = ""
    subject_prefix: str = "【广发基金视角晨报】"
    send_time: time = SCHEDULE_TIME
    timezone: str = TIMEZONE
    preferences: UserPreferences = field(default_factory=UserPreferences)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional["UserProfile"]:
        user_id = str(data.get("user_id", "")).strip()
        name = str(data.get("name", "")).strip()
        recipient_emails = _normalize_email_list(
            [str(item) for item in data.get("recipient_emails", [])]
        )

        if not user_id or not name or not recipient_emails:
            logger.warning("跳过无效用户配置: %s", data)
            return None

        return cls(
            user_id=user_id,
            name=name,
            recipient_emails=recipient_emails,
            enabled=bool(data.get("enabled", True)),
            smtp_server=str(data.get("smtp_server", "")).strip(),
            smtp_port=_parse_optional_int(data.get("smtp_port")),
            smtp_use_ssl=_parse_optional_bool(data.get("smtp_use_ssl")),
            sender_email=str(data.get("sender_email", "")).strip(),
            sender_password=str(data.get("sender_password", "")).strip(),
            sender_name=str(data.get("sender_name", SENDER_NAME)).strip() or SENDER_NAME,
            reply_to=str(data.get("reply_to", "")).strip(),
            subject_prefix=str(data.get("subject_prefix", "【广发基金视角晨报】")).strip() or "【广发基金视角晨报】",
            send_time=_parse_time(data.get("send_time"), SCHEDULE_TIME),
            timezone=str(data.get("timezone", TIMEZONE)).strip() or TIMEZONE,
            preferences=UserPreferences.from_dict(data.get("preferences")),
        )


def build_default_user_profile() -> UserProfile:
    """构建兼容旧配置的默认用户"""

    return UserProfile(
        user_id="default",
        name="默认订阅用户",
        recipient_emails=_normalize_email_list(RECIPIENT_EMAILS),
        enabled=True,
        smtp_server="",
        smtp_port=None,
        smtp_use_ssl=None,
        sender_email="",
        sender_password="",
        sender_name=SENDER_NAME,
        reply_to="",
        subject_prefix="【广发基金视角晨报】",
        send_time=SCHEDULE_TIME,
        timezone=TIMEZONE,
        preferences=UserPreferences(),
    )


def load_user_profiles(config_path: Optional[str] = None) -> List[UserProfile]:
    """加载用户配置；若不存在则回退到旧版单用户配置"""

    path = config_path or DEFAULT_USER_CONFIG_PATH
    if not os.path.exists(path):
        logger.info("未找到用户配置文件 %s，使用默认单用户配置", path)
        return [build_default_user_profile()]

    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)

    raw_users = payload.get("users", [])
    profiles: List[UserProfile] = []
    for item in raw_users:
        if not isinstance(item, dict):
            logger.warning("跳过非对象用户配置: %r", item)
            continue

        profile = UserProfile.from_dict(item)
        if profile:
            profiles.append(profile)

    if not profiles:
        logger.warning("用户配置文件 %s 中没有有效用户，回退到默认单用户配置", path)
        return [build_default_user_profile()]

    return profiles
