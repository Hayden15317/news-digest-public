"""
新闻分类模块 - 负责根据关键词对新闻进行分类
"""

import logging
from typing import Dict, List, Tuple
from fetcher import NewsItem

logger = logging.getLogger(__name__)


class NewsClassifier:
    """新闻分类器"""

    CATEGORY_BOOST = {
        "行业新闻": 8,
        "金融新闻": 5,
        "时政新闻": 4,
    }

    # 分类关键词映射
    KEYWORDS_MAP = {
        "行业新闻": {
            "证券": [
                "证券", "券商", "投行", "IPO", "上市", "股票", "股市",
                "交易所", "证监会", "融资融券", "打新", "中签", "涨停",
                "跌停", "牛市", "熊市", "大盘", "股指", "上证指数",
                "深成指", "创业板", "科创板", "新三板"
            ],
            "基金": [
                "基金", "公募基金", "私募基金", "货币基金", "债券基金",
                "股票基金", "指数基金", "ETF", "LOF", "分级基金",
                "FOF", "基金经理", "基金公司", "申购", "赎回", "净值",
                "累计净值", "七日年化", "万份收益"
            ],
            "A股": [
                "A股", "沪深", "上证指数", "深证成指", "创业板指",
                "科创50", "沪深300", "上证50", "中证500", "茅指数",
                "宁组合", "白马股", "蓝筹股", "概念股", "题材股",
                "次新股", "ST股", "退市", "停牌", "复牌"
            ],
            "港股": [
                "港股", "香港股市", "恒生指数", "恒生科技", "国企指数",
                "红筹股", "H股", "港股通", "南下资金", "北水",
                "香港交易所", "港交所", "恒指", "港股打新", "暗盘"
            ],
        },
        "金融新闻": {
            "行情": [
                "行情", "走势", "盘面", "技术分析", "K线", "均线",
                "MACD", "KDJ", "RSI", "布林线", "成交量", "成交额",
                "换手率", "市盈率", "市净率", "股息率", "振幅",
                "资金流向", "主力", "散户", "看多", "看空"
            ],
            "宏观经济": [
                "宏观经济", "GDP", "国内生产总值", "CPI", "PPI",
                "PMI", "工业增加值", "固定资产投资", "社会消费品零售",
                "进出口", "贸易顺差", "外汇储备", "M2", "社融",
                " economic growth", "recession", "inflation", "deflation"
            ],
            "利率": [
                "利率", "利息", "基准利率", "LPR", "MLF", "逆回购",
                "存款准备金率", "降息", "加息", "货币政策", "宽松",
                "紧缩", "流动性", "资金成本", "收益率曲线", "实际利率",
                "名义利率", "负利率"
            ],
            "汇率": [
                "汇率", "人民币", "美元", "欧元", "日元", "英镑",
                "美元指数", "离岸人民币", "在岸人民币", "中间价",
                "升值", "贬值", "外汇储备", "汇率操纵", "货币战争",
                "固定汇率", "浮动汇率", "钉住汇率"
            ],
        },
        "时政新闻": {
            "央行": [
                "央行", "中央银行", "中国人民银行", "美联储", "欧央行",
                "日本央行", "英国央行", "货币政策委员会", "行长",
                "利率决议", "政策声明", "新闻发布会", "金融稳定",
                "最后贷款人", "宏观审慎", "逆周期调节"
            ],
            "财政部": [
                "财政部", "财政部部长", "财政政策", "预算", "赤字",
                "国债", "地方债", "专项债", "税收政策", "减税降费",
                "转移支付", "政府采购", "国有资本", "主权财富基金"
            ],
            "证监会": [
                "证监会", "中国证监会", "证券监督管理委员会", "资本市场",
                "公募基金", "REITs", "并购重组", "基金销售费用",
                "上市公司监管", "信息披露", "投资者保护", "发行上市"
            ],
            "人大": [
                "人大", "全国人大", "人大常委会", "立法", "修法",
                "审议", "表决", "代表", "议案", "质询", "政府工作报告",
                "预算报告", "两高报告", "选举", "任命"
            ],
        },
    }

    def __init__(self):
        self.category_keywords = self._flatten_keywords()

    def _flatten_keywords(self) -> Dict[str, tuple]:
        """
        将关键词映射扁平化，便于快速查找
        返回: {关键词: (主类别, 子类别)}
        """
        flat_map = {}
        for main_cat, subcats in self.KEYWORDS_MAP.items():
            for subcat, keywords in subcats.items():
                for keyword in keywords:
                    flat_map[keyword.lower()] = (main_cat, subcat)
        return flat_map

    def classify_news(self, news_item: NewsItem) -> NewsItem:
        """
        对单条新闻进行分类
        """
        # 合并标题和摘要用于分类
        text = f"{news_item.title} {news_item.summary} {news_item.content}".lower()

        # 记录每个类别的匹配次数
        category_scores: Dict[Tuple[str, str], int] = {}

        # 对抓取阶段已经定好的类别给一个基础分，避免高质量国内源被随意改类
        if (
            news_item.category in self.KEYWORDS_MAP
            and news_item.subcategory in self.KEYWORDS_MAP[news_item.category]
        ):
            seed_key = (news_item.category, news_item.subcategory)
            category_scores[seed_key] = self.CATEGORY_BOOST.get(news_item.category, 3)

        for keyword, (main_cat, subcat) in self.category_keywords.items():
            if keyword in text:
                key = (main_cat, subcat)
                boost = 3 if main_cat == "行业新闻" else 2
                category_scores[key] = category_scores.get(key, 0) + boost

        if category_scores:
            # 选择匹配度最高的类别
            best_match = max(category_scores.items(), key=lambda x: x[1])
            (main_cat, subcat), score = best_match

            # 更新新闻类别
            news_item.category = main_cat
            news_item.subcategory = subcat

            logger.debug(f"新闻 '{news_item.title[:30]}...' 分类为: {main_cat}/{subcat} (匹配度: {score})")
        else:
            # 无法分类，标记为"其他"
            news_item.category = "其他"
            news_item.subcategory = "未分类"
            logger.debug(f"新闻 '{news_item.title[:30]}...' 无法分类")

        return news_item

    def classify_all_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        对所有新闻进行分类
        """
        logger.info(f"开始对 {len(news_items)} 条新闻进行分类...")

        classified_items = []
        for item in news_items:
            classified_item = self.classify_news(item)
            classified_items.append(classified_item)

        # 统计分类结果
        category_stats = {}
        for item in classified_items:
            key = f"{item.category}/{item.subcategory}"
            category_stats[key] = category_stats.get(key, 0) + 1

        logger.info("分类统计:")
        for cat, count in sorted(category_stats.items()):
            logger.info(f"  {cat}: {count}条")

        return classified_items

    def get_news_by_category(self, news_items: List[NewsItem], category: str) -> List[NewsItem]:
        """
        按主类别筛选新闻
        """
        return [item for item in news_items if item.category == category]

    def get_news_by_subcategory(self, news_items: List[NewsItem], subcategory: str) -> List[NewsItem]:
        """
        按子类别筛选新闻
        """
        return [item for item in news_items if item.subcategory == subcategory]


def classify_news(news_items: List[NewsItem]) -> List[NewsItem]:
    """
    便捷函数：对新闻进行分类
    """
    classifier = NewsClassifier()
    return classifier.classify_all_news(news_items)


if __name__ == "__main__":
    # 测试分类功能
    from fetcher import fetch_news

    # 先抓取新闻
    news = fetch_news()

    # 然后分类
    classifier = NewsClassifier()
    classified_news = classifier.classify_all_news(news)

    # 输出结果
    print("\n分类结果示例:")
    for item in classified_news[:5]:
        print(f"\n标题: {item.title}")
        print(f"分类: {item.category} > {item.subcategory}")
        print(f"时间: {item.published}")
        print("-" * 80)
