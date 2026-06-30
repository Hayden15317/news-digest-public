"""
自动新闻邮件推送系统 - 主程序

功能：
1. 抓取RSS新闻
2. 对新闻进行分类
3. 生成新闻摘要
4. 发送HTML邮件
5. 支持定时运行

运行方式：
- 立即运行一次：python main.py --once
- 定时运行（每天早上8点）：python main.py
"""

import argparse
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 导入配置
from config import (
    SCHEDULE_TIME, TIMEZONE, LOG_LEVEL, LOG_FILE
)

# 导入各个模块
from fetcher import NewsFetcher, NewsItem
from classifier import NewsClassifier
from summarizer import NewsSummarizer
from news_filter import UserNewsFilter
from sender import EmailDeliveryConfig, EmailSender
from user_config import DEFAULT_USER_CONFIG_PATH, UserProfile, load_user_profiles


# 设置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NewsEmailSystem:
    """新闻邮件系统主类"""

    def __init__(self, user_config_path: Optional[str] = None):
        self.fetcher = NewsFetcher()
        self.classifier = NewsClassifier()
        self.summarizer = NewsSummarizer()
        self.news_filter = UserNewsFilter()
        self.scheduler = None
        self.running = False
        self.user_config_path = user_config_path

    def load_active_profiles(self, user_ids: Optional[List[str]] = None) -> List[UserProfile]:
        profiles = [profile for profile in load_user_profiles(self.user_config_path) if profile.enabled]
        if user_ids:
            user_id_set = {user_id.strip() for user_id in user_ids if user_id.strip()}
            profiles = [profile for profile in profiles if profile.user_id in user_id_set]
        return profiles

    def _build_sender_for_profile(self, profile: UserProfile) -> EmailSender:
        delivery_kwargs = {
            "sender_name": profile.sender_name,
            "recipient_emails": profile.recipient_emails,
            "reply_to": profile.reply_to,
            "subject_prefix": profile.subject_prefix,
            "report_slug": profile.user_id,
        }

        if profile.smtp_server:
            delivery_kwargs["smtp_server"] = profile.smtp_server
        if profile.smtp_port is not None:
            delivery_kwargs["smtp_port"] = profile.smtp_port
        if profile.smtp_use_ssl is not None:
            delivery_kwargs["use_ssl"] = profile.smtp_use_ssl
        if profile.sender_email:
            delivery_kwargs["sender_email"] = profile.sender_email
        if profile.sender_password:
            delivery_kwargs["sender_password"] = profile.sender_password

        delivery_config = EmailDeliveryConfig(
            **delivery_kwargs
        )
        return EmailSender(delivery_config=delivery_config)

    def _prepare_news(self) -> List[NewsItem]:
        logger.info("步骤 1/4: 抓取新闻...")
        news_items = self.fetcher.fetch_all_news()
        if not news_items:
            logger.warning("没有抓取到任何新闻")
            return []
        logger.info("成功抓取 %s 条新闻", len(news_items))

        logger.info("步骤 2/4: 分类新闻...")
        news_items = self.classifier.classify_all_news(news_items)
        logger.info("新闻分类完成")

        logger.info("步骤 3/4: 生成摘要...")
        news_items = self.summarizer.generate_summaries(news_items)
        logger.info("摘要生成完成")
        return news_items

    def _send_to_profiles(self, news_items: List[NewsItem], profiles: List[UserProfile], run_date: datetime) -> bool:
        if not profiles:
            logger.warning("没有可发送的启用用户")
            return False

        success_count = 0
        attempted_count = 0

        logger.info("步骤 4/4: 按用户配置发送邮件...")
        for profile in profiles:
            filtered_items = self.news_filter.filter_for_user(news_items, profile)

            if not filtered_items and not profile.preferences.send_empty_email:
                logger.info("用户 %s 无匹配新闻，已跳过发送", profile.user_id)
                continue

            attempted_count += 1
            logger.info(
                "用户 %s 准备发送 %s 条新闻到 %s",
                profile.user_id,
                len(filtered_items),
                ", ".join(profile.recipient_emails),
            )

            sender = self._build_sender_for_profile(profile)
            report_info = sender.export_web_report(filtered_items, run_date)
            if report_info.get("written_paths"):
                logger.info(
                    "用户 %s 已更新晨报网页: %s",
                    profile.user_id,
                    report_info["written_paths"],
                )
            if report_info.get("public_report_url"):
                logger.info(
                    "用户 %s 公网晨报地址: %s",
                    profile.user_id,
                    report_info["public_report_url"],
                )
            if sender.send_news_email(filtered_items, run_date):
                success_count += 1
            else:
                logger.error("用户 %s 邮件发送失败", profile.user_id)

        if attempted_count == 0:
            logger.warning("所有用户均无匹配新闻，未实际发送邮件")
            return False

        logger.info("本次成功发送 %s/%s 个用户版本", success_count, attempted_count)
        return success_count == attempted_count

    def run_once(self, user_ids: Optional[List[str]] = None) -> bool:
        """
        运行一次完整的新闻抓取和发送流程
        
        Returns:
            bool: 是否成功
        """
        try:
            start_time = datetime.now()
            logger.info("=" * 60)
            logger.info("开始执行新闻推送任务")
            logger.info("=" * 60)

            profiles = self.load_active_profiles(user_ids)
            if not profiles:
                logger.warning("没有找到启用的用户配置")
                return False

            news_items = self._prepare_news()
            if not news_items:
                return False

            success = self._send_to_profiles(news_items, profiles, start_time)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if success:
                logger.info("=" * 60)
                logger.info(f"任务执行成功！耗时: {duration:.2f}秒")
                logger.info("=" * 60)
                return True
            else:
                logger.error("邮件发送失败")
                return False

        except Exception as e:
            logger.exception(f"任务执行过程中发生错误: {str(e)}")
            return False

    def preview_for_profiles(self, user_ids: Optional[List[str]] = None) -> bool:
        profiles = self.load_active_profiles(user_ids)
        if not profiles:
            logger.warning("没有找到启用的用户配置")
            return False

        news_items = self._prepare_news()
        if not news_items:
            return False

        print("\n" + "=" * 60)
        print(f"共抓取 {len(news_items)} 条新闻")
        print("=" * 60)

        for profile in profiles:
            filtered_items = self.news_filter.filter_for_user(news_items, profile)
            sender = self._build_sender_for_profile(profile)
            report_info = sender.export_web_report(filtered_items, datetime.now())
            send_time_text = (
                profile.send_time.strftime('%H:%M')
                if getattr(profile, "send_time", None) is not None
                else "未设置"
            )
            print(f"\n用户: {profile.name} ({profile.user_id})")
            print(f"收件人: {', '.join(profile.recipient_emails)}")
            print(f"计划发送时间: {send_time_text} {profile.timezone}")
            print(f"命中新闻数: {len(filtered_items)}")
            if report_info.get("local_report_url"):
                print(f"本地晨报页: {report_info['local_report_url']}")
            if report_info.get("public_report_url"):
                print(f"公网晨报页: {report_info['public_report_url']}")
            for index, item in enumerate(filtered_items[:5], 1):
                print(f"  {index}. [{item.category}/{item.subcategory}] {item.title}")

        return True

    def _group_profiles_by_schedule(self, profiles: List[UserProfile]) -> Dict[Tuple[str, int, int], List[UserProfile]]:
        grouped: Dict[Tuple[str, int, int], List[UserProfile]] = {}
        for profile in profiles:
            key = (profile.timezone, profile.send_time.hour, profile.send_time.minute)
            grouped.setdefault(key, []).append(profile)
        return grouped

    def start_scheduler(self):
        """
        启动定时调度器
        """
        try:
            profiles = self.load_active_profiles()
            if not profiles:
                raise ValueError("没有可用的启用用户配置")

            self.scheduler = BackgroundScheduler(timezone=pytz.timezone(TIMEZONE))

            grouped_profiles = self._group_profiles_by_schedule(profiles)
            for (timezone_name, hour, minute), members in grouped_profiles.items():
                timezone = pytz.timezone(timezone_name)
                trigger = CronTrigger(
                    hour=hour,
                    minute=minute,
                    second=0,
                    timezone=timezone,
                )
                user_ids = [profile.user_id for profile in members]
                job_id = f"news_email_job_{timezone_name}_{hour:02d}_{minute:02d}".replace("/", "_")

                self.scheduler.add_job(
                    func=self.run_once,
                    trigger=trigger,
                    kwargs={"user_ids": user_ids},
                    id=job_id,
                    name=f"新闻邮件推送任务 {hour:02d}:{minute:02d}",
                    replace_existing=True
                )

            self.scheduler.start()
            self.running = True

            logger.info("=" * 60)
            logger.info("定时调度器已启动")
            for job in self.scheduler.get_jobs():
                logger.info("任务 %s 下次运行时间: %s", job.id, job.next_run_time)
            logger.info("=" * 60)

            # 注册信号处理
            self._register_signal_handlers()

        except Exception as e:
            logger.exception(f"启动调度器时发生错误: {str(e)}")
            raise

    def stop_scheduler(self):
        """
        停止定时调度器
        """
        if self.scheduler:
            self.scheduler.shutdown()
            self.running = False
            logger.info("定时调度器已停止")

    def _register_signal_handlers(self):
        """
        注册信号处理程序
        """
        def signal_handler(signum, frame):
            logger.info(f"接收到信号 {signum}，正在停止...")
            self.stop_scheduler()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


def main():
    """
    主函数
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='自动新闻邮件推送系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 立即运行一次
  python main.py --once
  
  # 启动定时调度（每天早上8点运行）
  python main.py
  
  # 使用指定的用户配置文件
  python main.py --user-config ./users.json

  # 仅预览某个用户会收到哪些新闻
  python main.py --test --user research-team
        """
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='立即运行一次，不启动定时调度'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='测试模式：抓取新闻并按用户展示命中结果，不发送邮件'
    )

    parser.add_argument(
        '--user-config',
        default=DEFAULT_USER_CONFIG_PATH,
        help=f'用户配置文件路径，默认: {DEFAULT_USER_CONFIG_PATH}'
    )

    parser.add_argument(
        '--user',
        action='append',
        help='只处理指定 user_id，可重复传入多个'
    )

    args = parser.parse_args()

    # 创建系统实例
    user_config_path = args.user_config
    if user_config_path and not os.path.isabs(user_config_path):
        user_config_path = os.path.abspath(user_config_path)

    system = NewsEmailSystem(user_config_path=user_config_path)

    if args.test:
        logger.info("=" * 60)
        logger.info("运行测试模式（不发送邮件）")
        logger.info("=" * 60)
        success = system.preview_for_profiles(args.user)
        sys.exit(0 if success else 1)

    elif args.once:
        # 立即运行一次
        success = system.run_once(args.user)
        sys.exit(0 if success else 1)

    else:
        # 启动定时调度
        try:
            system.start_scheduler()

            # 保持程序运行
            while system.running:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("接收到键盘中断，正在停止...")
            system.stop_scheduler()
            sys.exit(0)


if __name__ == "__main__":
    main()
