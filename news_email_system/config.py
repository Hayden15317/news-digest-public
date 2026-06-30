"""
配置文件 - 自动新闻邮件推送系统
"""

import os
from datetime import time

# ==========================================
# 邮件配置
# ==========================================

# SMTP服务器配置
# QQ邮箱: smtp.qq.com, 端口: 465 (SSL) 或 587 (TLS)
# 163邮箱: smtp.163.com, 端口: 465 (SSL)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.163.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "true").lower() == "true"

# 发件人配置
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "Hayden15317@163.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "LNZ4jktcyssRNtv4")  # 授权码，非邮箱密码
SENDER_NAME = os.getenv("SENDER_NAME", "新闻推送助手")

# 收件人配置 (多个收件人用逗号分隔)
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "Hayden15317@163.com").split(",")

# 公网晨报页面地址配置
# GitHub Pages 示例:
# https://<github-username>.github.io/<repo-name>
PUBLIC_REPORT_SITE_URL = os.getenv("PUBLIC_REPORT_SITE_URL", "").strip().rstrip("/")


# ==========================================
# 国内优先新闻源配置
# ==========================================

# 说明：
# 1. 优先使用国内公开 RSS / 公开网页 / 公开 JSON 接口。
# 2. 行业新闻使用更高优先级和更大抓取额度。
# 3. 同一个公开接口可以配置成多个“专题源”，通过关键词映射到不同子类别。
NEWS_SOURCE_CONFIGS = [
    {
        "name": "基金业协会-协会要闻",
        "type": "html_list",
        "url": "https://www.amac.org.cn/xwfb/xhyw/",
        "base_url": "https://www.amac.org.cn",
        "category": "行业新闻",
        "subcategory": "基金TA",
        "priority": 126,
        "domestic": True,
        "limit": 10,
        "days_limit": 30,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/xwfb/xhyw/']",
        ],
        "link_patterns": ["/xwfb/xhyw/"],
        "keywords": [
            "基金", "公募基金", "私募基金", "基金销售", "销售机构", "信息披露",
            "份额登记", "登记结算", "清算", "托管", "估值", "直销", "代销",
            "账户", "开户", "过户", "投资者服务", "基金从业", "中基协"
        ],
    },
    {
        "name": "基金业协会-通知公告",
        "type": "html_list",
        "url": "https://www.amac.org.cn/xwfb/tzgg/",
        "base_url": "https://www.amac.org.cn",
        "category": "行业新闻",
        "subcategory": "基金TA",
        "priority": 124,
        "domestic": True,
        "limit": 10,
        "days_limit": 30,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/xwfb/tzgg/']",
        ],
        "link_patterns": ["/xwfb/tzgg/"],
        "keywords": [
            "基金销售", "销售机构", "信息披露", "份额登记", "登记结算", "清算",
            "托管", "估值", "直销", "代销", "基金账户", "投资者服务",
            "系统", "规范", "公告", "基金从业", "中基协"
        ],
    },
    {
        "name": "中国结算-要闻动态",
        "type": "html_list",
        "url": "http://www.chinaclear.cn/zdjs/gsdtnew/about_gsdt.shtml",
        "base_url": "http://www.chinaclear.cn",
        "category": "行业新闻",
        "subcategory": "基金TA",
        "priority": 128,
        "domestic": True,
        "limit": 10,
        "days_limit": 30,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/zdjs/gsdtnew/']",
        ],
        "link_patterns": ["/zdjs/gsdtnew/"],
        "keywords": [
            "中国结算", "中证登", "登记结算", "清算交收", "份额登记", "过户",
            "基金", "ETF", "REITs", "账户", "开户", "结算", "交收",
            "直销服务平台", "投资者服务"
        ],
    },
    {
        "name": "中国结算-通知公告",
        "type": "html_list",
        "url": "http://www.chinaclear.cn/zdjs/xtzgg/center_flist.shtml",
        "base_url": "http://www.chinaclear.cn",
        "category": "行业新闻",
        "subcategory": "基金TA",
        "priority": 123,
        "domestic": True,
        "limit": 10,
        "days_limit": 30,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/zdjs/']",
        ],
        "link_patterns": ["/zdjs/"],
        "keywords": [
            "中国结算", "中证登", "登记结算", "清算交收", "结算业务",
            "证券资金结算", "基金", "ETF", "REITs", "账户", "开户",
            "过户", "基金E账户", "直销服务平台"
        ],
    },
    {
        "name": "财联社-证券电报",
        "type": "cls_api",
        "url": "https://www.cls.cn/nodeapi/telegraphList",
        "web_url": "https://www.cls.cn/telegraph",
        "category": "行业新闻",
        "subcategory": "证券",
        "priority": 120,
        "domestic": True,
        "limit": 20,
        "params": {
            "app": "CailianpressWeb",
            "os": "web",
            "refresh_type": "1",
            "order": "1",
            "rn": "60",
            "sv": "8.4.6",
        },
        "headers": {
            "Referer": "https://www.cls.cn/telegraph",
        },
        "keywords": [
            "证券", "券商", "证监会", "交易所", "并购", "上市", "IPO",
            "再融资", "减持", "停牌", "复牌", "公告"
        ],
    },
    {
        "name": "财联社-基金电报",
        "type": "cls_api",
        "url": "https://www.cls.cn/nodeapi/telegraphList",
        "web_url": "https://www.cls.cn/telegraph",
        "category": "行业新闻",
        "subcategory": "基金",
        "priority": 118,
        "domestic": True,
        "limit": 18,
        "params": {
            "app": "CailianpressWeb",
            "os": "web",
            "refresh_type": "1",
            "order": "1",
            "rn": "60",
            "sv": "8.4.6",
        },
        "headers": {
            "Referer": "https://www.cls.cn/telegraph",
        },
        "keywords": [
            "基金", "公募", "私募", "ETF", "REITs", "FOF", "基金经理",
            "申购", "赎回", "净值"
        ],
    },
    {
        "name": "财联社-A股电报",
        "type": "cls_api",
        "url": "https://www.cls.cn/nodeapi/telegraphList",
        "web_url": "https://www.cls.cn/telegraph",
        "category": "行业新闻",
        "subcategory": "A股",
        "priority": 125,
        "domestic": True,
        "limit": 24,
        "params": {
            "app": "CailianpressWeb",
            "os": "web",
            "refresh_type": "1",
            "order": "1",
            "rn": "80",
            "sv": "8.4.6",
        },
        "headers": {
            "Referer": "https://www.cls.cn/telegraph",
        },
        "keywords": [
            "A股", "沪指", "深成指", "创业板", "科创板", "北证",
            "沪深", "两市", "涨停", "跌停", "龙虎榜", "融资余额"
        ],
    },
    {
        "name": "财联社-港股电报",
        "type": "cls_api",
        "url": "https://www.cls.cn/nodeapi/telegraphList",
        "web_url": "https://www.cls.cn/telegraph",
        "category": "行业新闻",
        "subcategory": "港股",
        "priority": 116,
        "domestic": True,
        "limit": 16,
        "params": {
            "app": "CailianpressWeb",
            "os": "web",
            "refresh_type": "1",
            "order": "1",
            "rn": "80",
            "sv": "8.4.6",
        },
        "headers": {
            "Referer": "https://www.cls.cn/telegraph",
        },
        "keywords": [
            "港股", "恒生", "恒指", "港交所", "南向资金", "港股通", "H股"
        ],
    },
    {
        "name": "证券时报-要闻",
        "type": "html_list",
        "url": "https://www.stcn.com/article/list/yw.html",
        "base_url": "https://www.stcn.com",
        "category": "行业新闻",
        "subcategory": "A股",
        "priority": 112,
        "domestic": True,
        "limit": 12,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/article/detail/']",
        ],
        "link_patterns": ["/article/detail/"],
        "keywords": [
            "A股", "资本市场", "券商", "上市公司", "证监会", "基金", "港股"
        ],
    },
    {
        "name": "证券时报-首页精选",
        "type": "html_list",
        "url": "https://www.stcn.com/",
        "base_url": "https://www.stcn.com",
        "category": "行业新闻",
        "subcategory": "证券",
        "priority": 109,
        "domestic": True,
        "limit": 10,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/article/detail/']",
        ],
        "link_patterns": ["/article/detail/"],
        "keywords": [
            "A股", "券商", "基金", "资本市场", "港股", "上市公司", "交易所"
        ],
    },
    {
        "name": "证券时报-首页港股",
        "type": "html_list",
        "url": "https://www.stcn.com/",
        "base_url": "https://www.stcn.com",
        "category": "行业新闻",
        "subcategory": "港股",
        "priority": 105,
        "domestic": True,
        "limit": 8,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/article/detail/']",
        ],
        "link_patterns": ["/article/detail/"],
        "keywords": [
            "港股", "恒生", "恒指", "港交所", "南向资金", "港股通"
        ],
    },
    {
        "name": "证券时报-基金",
        "type": "html_list",
        "url": "https://www.stcn.com/article/list/fund.html",
        "base_url": "https://www.stcn.com",
        "category": "行业新闻",
        "subcategory": "基金",
        "priority": 110,
        "domestic": True,
        "limit": 10,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/article/detail/']",
        ],
        "link_patterns": ["/article/detail/"],
        "keywords": [
            "基金", "公募", "ETF", "REITs", "基金经理", "持仓"
        ],
    },
    {
        "name": "证券时报-公司新闻",
        "type": "html_list",
        "url": "https://www.stcn.com/article/list/gsxw.html",
        "base_url": "https://www.stcn.com",
        "category": "行业新闻",
        "subcategory": "证券",
        "priority": 108,
        "domestic": True,
        "limit": 10,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/article/detail/']",
        ],
        "link_patterns": ["/article/detail/"],
        "keywords": [
            "上市公司", "定增", "并购", "券商", "披露", "监管", "回购"
        ],
    },
    {
        "name": "中国证券报-基金快讯",
        "type": "html_list",
        "url": "https://www.cs.com.cn/sylm/jsbd/list.html",
        "base_url": "https://www.cs.com.cn",
        "category": "行业新闻",
        "subcategory": "基金",
        "priority": 114,
        "domestic": True,
        "limit": 10,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "link_selectors": [
            "a[href]",
        ],
        "keywords": [
            "基金", "公募", "ETF", "基金经理", "持有期基金", "REITs", "QDII"
        ],
    },
    {
        "name": "中国证券报-资本市场快讯",
        "type": "html_list",
        "url": "https://www.cs.com.cn/sylm/jsbd/list.html",
        "base_url": "https://www.cs.com.cn",
        "category": "行业新闻",
        "subcategory": "证券",
        "priority": 113,
        "domestic": True,
        "limit": 10,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "link_selectors": [
            "a[href]",
        ],
        "keywords": [
            "券商", "资本市场", "上市公司", "IPO", "两融", "并购重组", "证券"
        ],
    },
    {
        "name": "中国证券报-宏观政策快讯",
        "type": "html_list",
        "url": "https://www.cs.com.cn/sylm/jsbd/list.html",
        "base_url": "https://www.cs.com.cn",
        "category": "金融新闻",
        "subcategory": "宏观经济",
        "priority": 100,
        "domestic": True,
        "limit": 10,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "link_selectors": [
            "a[href]",
        ],
        "keywords": [
            "宏观", "经济", "货币政策", "财政政策", "人民币", "社融", "利率"
        ],
    },
    {
        "name": "上海证券报-基金与配置",
        "type": "html_list",
        "url": "https://www.cnstock.com/",
        "base_url": "https://www.cnstock.com",
        "category": "行业新闻",
        "subcategory": "基金",
        "priority": 111,
        "domestic": True,
        "limit": 8,
        "strict_keywords": True,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href]",
        ],
        "keywords": [
            "基金", "ETF", "资管", "配置", "私募", "公募", "理财"
        ],
    },
    {
        "name": "上海证券报-证券与港股",
        "type": "html_list",
        "url": "https://www.cnstock.com/",
        "base_url": "https://www.cnstock.com",
        "category": "行业新闻",
        "subcategory": "港股",
        "priority": 108,
        "domestic": True,
        "limit": 8,
        "strict_keywords": True,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href]",
        ],
        "keywords": [
            "港股", "券商股", "A股", "两融", "资金风向标", "资本市场"
        ],
    },
    {
        "name": "上海证券报-宏观与利率",
        "type": "html_list",
        "url": "https://www.cnstock.com/",
        "base_url": "https://www.cnstock.com",
        "category": "金融新闻",
        "subcategory": "宏观经济",
        "priority": 99,
        "domestic": True,
        "limit": 8,
        "strict_keywords": True,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href]",
        ],
        "keywords": [
            "国家统计局", "人民币", "中间价", "利率", "宏观", "地方债", "经济"
        ],
    },
    {
        "name": "东方财富-基金与ETF",
        "type": "html_list",
        "url": "https://fund.eastmoney.com/a/cjjyw.html",
        "base_url": "https://fund.eastmoney.com",
        "category": "行业新闻",
        "subcategory": "基金",
        "priority": 112,
        "domestic": True,
        "limit": 10,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "li > a[href$='.html']",
        ],
        "link_patterns": [".html"],
        "keywords": [
            "公募", "基金", "ETF", "FOF", "REITs", "基金经理", "QDII", "发行"
        ],
    },
    {
        "name": "东方财富-交易与券商",
        "type": "html_list",
        "url": "https://money.eastmoney.com/a/cjjlc.html",
        "base_url": "https://money.eastmoney.com",
        "category": "行业新闻",
        "subcategory": "证券",
        "priority": 109,
        "domestic": True,
        "limit": 8,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "li > a[href$='.html']",
        ],
        "link_patterns": [".html"],
        "keywords": [
            "券商", "证券", "两融", "A股", "ETF", "资金流向", "基金发行", "公募"
        ],
    },
    {
        "name": "21财经-基金发行与资管",
        "type": "html_list",
        "url": "https://www.21jingji.com/channel/finance",
        "base_url": "https://m.21jingji.com",
        "category": "行业新闻",
        "subcategory": "基金",
        "priority": 107,
        "domestic": True,
        "limit": 8,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/article/']",
        ],
        "link_patterns": ["/article/"],
        "keywords": [
            "基金", "公募", "资管", "ETF", "发行", "券商资管", "理财"
        ],
    },
    {
        "name": "21财经-宏观与市场",
        "type": "html_list",
        "url": "https://www.21jingji.com/channel/finance",
        "base_url": "https://m.21jingji.com",
        "category": "金融新闻",
        "subcategory": "宏观经济",
        "priority": 98,
        "domestic": True,
        "limit": 8,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/article/']",
        ],
        "link_patterns": ["/article/"],
        "keywords": [
            "央行", "MLF", "利率", "汇率", "宏观", "债市", "人民币", "资管"
        ],
    },
    {
        "name": "券商中国-首页精选",
        "type": "html_list",
        "url": "https://www.zqcn.com/",
        "base_url": "https://www.zqcn.com",
        "category": "行业新闻",
        "subcategory": "证券",
        "priority": 97,
        "domestic": True,
        "limit": 8,
        "strict_keywords": True,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href]",
        ],
        "keywords": [
            "券商", "基金", "ETF", "发行", "资本市场", "并购重组", "公募", "港股"
        ],
    },
    {
        "name": "证券时报-快讯宏观",
        "type": "html_list",
        "url": "https://www.stcn.com/article/list/kx.html",
        "base_url": "https://www.stcn.com",
        "category": "金融新闻",
        "subcategory": "宏观经济",
        "priority": 102,
        "domestic": True,
        "limit": 10,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/article/detail/']",
        ],
        "link_patterns": ["/article/detail/"],
        "keywords": [
            "经济", "宏观", "GDP", "CPI", "PPI", "PMI", "社融", "消费",
            "制造业", "发改委", "财政政策", "货币政策"
        ],
    },
    {
        "name": "证券时报-快讯政策",
        "type": "html_list",
        "url": "https://www.stcn.com/article/list/kx.html",
        "base_url": "https://www.stcn.com",
        "category": "时政新闻",
        "subcategory": "央行",
        "priority": 101,
        "domestic": True,
        "limit": 8,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/article/detail/']",
        ],
        "link_patterns": ["/article/detail/"],
        "keywords": [
            "中国人民银行", "财政部", "证监会", "金融监管总局", "国务院",
            "国新办", "央行", "公告", "政策"
        ],
    },
    {
        "name": "财联社-宏观快讯",
        "type": "cls_api",
        "url": "https://www.cls.cn/nodeapi/telegraphList",
        "web_url": "https://www.cls.cn/telegraph",
        "category": "金融新闻",
        "subcategory": "宏观经济",
        "priority": 86,
        "domestic": True,
        "limit": 16,
        "params": {
            "app": "CailianpressWeb",
            "os": "web",
            "refresh_type": "1",
            "order": "1",
            "rn": "60",
            "sv": "8.4.6",
        },
        "headers": {
            "Referer": "https://www.cls.cn/telegraph",
        },
        "keywords": [
            "宏观", "经济", "GDP", "CPI", "PPI", "PMI", "社融",
            "消费", "出口", "制造业", "工业增加值"
        ],
    },
    {
        "name": "财联社-利率快讯",
        "type": "cls_api",
        "url": "https://www.cls.cn/nodeapi/telegraphList",
        "web_url": "https://www.cls.cn/telegraph",
        "category": "金融新闻",
        "subcategory": "利率",
        "priority": 84,
        "domestic": True,
        "limit": 12,
        "params": {
            "app": "CailianpressWeb",
            "os": "web",
            "refresh_type": "1",
            "order": "1",
            "rn": "60",
            "sv": "8.4.6",
        },
        "headers": {
            "Referer": "https://www.cls.cn/telegraph",
        },
        "keywords": [
            "利率", "LPR", "MLF", "逆回购", "降息", "加息", "收益率"
        ],
    },
    {
        "name": "财联社-汇率快讯",
        "type": "cls_api",
        "url": "https://www.cls.cn/nodeapi/telegraphList",
        "web_url": "https://www.cls.cn/telegraph",
        "category": "金融新闻",
        "subcategory": "汇率",
        "priority": 82,
        "domestic": True,
        "limit": 10,
        "params": {
            "app": "CailianpressWeb",
            "os": "web",
            "refresh_type": "1",
            "order": "1",
            "rn": "60",
            "sv": "8.4.6",
        },
        "headers": {
            "Referer": "https://www.cls.cn/telegraph",
        },
        "keywords": [
            "汇率", "人民币", "美元指数", "中间价", "离岸人民币", "在岸人民币"
        ],
    },
    {
        "name": "财联社-央行快讯",
        "type": "cls_api",
        "url": "https://www.cls.cn/nodeapi/telegraphList",
        "web_url": "https://www.cls.cn/telegraph",
        "category": "时政新闻",
        "subcategory": "央行",
        "priority": 80,
        "domestic": True,
        "limit": 10,
        "params": {
            "app": "CailianpressWeb",
            "os": "web",
            "refresh_type": "1",
            "order": "1",
            "rn": "60",
            "sv": "8.4.6",
        },
        "headers": {
            "Referer": "https://www.cls.cn/telegraph",
        },
        "keywords": [
            "央行", "中国人民银行", "货币政策", "金融稳定", "存款准备金率"
        ],
    },
    {
        "name": "财政部-政策发布",
        "type": "html_list",
        "url": "https://www.mof.gov.cn/zhengwuxinxi/zhengcefabu/",
        "base_url": "http://www.mof.gov.cn",
        "category": "时政新闻",
        "subcategory": "财政部",
        "priority": 78,
        "domestic": True,
        "limit": 10,
        "days_limit": 14,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href]",
        ],
        "link_patterns": ["/zhengcefabu/", "/zcgz/", "/phjr/", "/gzdt/"],
        "keywords": [
            "财政部", "财政政策", "税收", "国债", "专项债", "预算", "贴息"
        ],
    },
    {
        "name": "中国政府网-政策库",
        "type": "html_list",
        "url": "https://www.gov.cn/zhengce/zhengceku/bmwj/home.htm",
        "base_url": "https://www.gov.cn",
        "category": "时政新闻",
        "subcategory": "人大",
        "priority": 72,
        "domestic": True,
        "limit": 10,
        "days_limit": 14,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href]",
        ],
        "link_patterns": ["/content_", "/zhengce/zhengceku/"],
        "keywords": [
            "国务院", "国务院办公厅", "政策", "实施意见", "通知", "决定",
            "全国人大", "人大常委会", "审议", "修订", "立法"
        ],
    },
    {
        "name": "中国政府网-要闻速览",
        "type": "html_list",
        "url": "https://www.gov.cn/yaowen/liebiao/",
        "base_url": "https://www.gov.cn",
        "category": "时政新闻",
        "subcategory": "民生",
        "priority": 110,
        "domestic": True,
        "limit": 12,
        "days_limit": 14,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href]",
        ],
        "link_patterns": ["/yaowen/liebiao/", "/lianbo/"],
        "keywords": [
            "要闻", "高温", "降雨", "台风", "医疗", "教育", "就业", "消费",
            "交通", "铁路", "住房", "养老", "社保", "应急", "救援", "民生"
        ],
    },
    {
        "name": "新华网-时政民生",
        "type": "html_list",
        "url": "https://www.news.cn/politics/",
        "base_url": "https://www.news.cn",
        "category": "时政新闻",
        "subcategory": "社会",
        "priority": 108,
        "domestic": True,
        "limit": 12,
        "days_limit": 14,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/politics/']",
            "a[href*='news.cn/politics/']",
        ],
        "link_patterns": ["/politics/"],
        "keywords": [
            "高温", "暴雨", "医疗", "教育", "儿童", "养老", "出行", "交通",
            "住房", "救援", "应急", "健康", "就业", "消费", "社会", "民生"
        ],
    },
    {
        "name": "中国新闻网-社会民生",
        "type": "html_list",
        "url": "https://www.chinanews.com.cn/society.shtml",
        "base_url": "https://www.chinanews.com.cn",
        "category": "时政新闻",
        "subcategory": "社会",
        "priority": 107,
        "domestic": True,
        "limit": 12,
        "days_limit": 14,
        "strict_keywords": True,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/sh/']",
            "a[href*='/jk/']",
            "a[href*='/life/']",
        ],
        "link_patterns": ["/sh/", "/jk/", "/life/"],
        "keywords": [
            "高温", "暴雨", "防汛", "医疗", "教育", "儿童", "养老", "社保",
            "就业", "消费", "住房", "出行", "铁路", "航班", "食品安全",
            "应急", "救援", "消防", "反诈", "诈骗", "民生", "社会"
        ],
    },
    {
        "name": "央视网-民生观察",
        "type": "html_list",
        "url": "https://news.cctv.com/",
        "base_url": "https://news.cctv.com",
        "category": "时政新闻",
        "subcategory": "民生",
        "priority": 105,
        "domestic": True,
        "limit": 12,
        "days_limit": 14,
        "strict_keywords": True,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='news.cctv.com/']",
            "a[href*='tv.cctv.com/']",
        ],
        "link_patterns": ["news.cctv.com/", "tv.cctv.com/"],
        "keywords": [
            "高温", "暴雨", "台风", "沙尘", "医疗", "健康", "教育", "就业",
            "住房", "养老", "出行", "交通", "食品安全", "医保", "药品",
            "反诈", "诈骗", "消防", "应急", "救援", "生活", "民生", "社会"
        ],
    },
    {
        "name": "国家发展改革委-新闻发布",
        "type": "html_list",
        "url": "https://www.ndrc.gov.cn/xwdt/xwfb/",
        "base_url": "https://www.ndrc.gov.cn",
        "category": "时政新闻",
        "subcategory": "发改委",
        "priority": 92,
        "domestic": True,
        "limit": 10,
        "days_limit": 14,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/xwdt/xwfb/']",
        ],
        "link_patterns": ["/xwdt/xwfb/"],
        "keywords": [
            "国家发展改革委", "发改委", "新闻发布", "政策", "通知", "实施意见",
            "规划", "价格", "投资", "就业", "产业", "能源", "消费", "经济"
        ],
    },
    {
        "name": "全国人大-立法动态",
        "type": "html_list",
        "url": "http://www.npc.gov.cn/c2/c183/c199/index.html",
        "base_url": "http://www.npc.gov.cn",
        "category": "时政新闻",
        "subcategory": "人大",
        "priority": 90,
        "domestic": True,
        "limit": 10,
        "days_limit": 14,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/c2/']",
            "a[href*='/npc/']",
        ],
        "link_patterns": ["/c2/", "/npc/"],
        "keywords": [
            "全国人大", "人大常委会", "立法", "法律草案", "审议", "修订",
            "决定", "法案", "征求意见", "施行"
        ],
    },
    {
        "name": "证监会-要闻发布",
        "type": "html_list",
        "url": "http://www.csrc.gov.cn/csrc/c100028/common_xq_list.shtml",
        "base_url": "http://www.csrc.gov.cn",
        "category": "时政新闻",
        "subcategory": "证监会",
        "priority": 103,
        "domestic": True,
        "limit": 10,
        "days_limit": 14,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/content.shtml']",
        ],
        "link_patterns": ["/content.shtml"],
        "keywords": [
            "中国证监会", "证监会", "基金", "REITs", "资本市场", "监管", "公告"
        ],
    },
    {
        "name": "人民银行-新闻发布",
        "type": "html_list",
        "url": "https://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html",
        "base_url": "https://www.pbc.gov.cn",
        "category": "金融新闻",
        "subcategory": "宏观经济",
        "priority": 96,
        "domestic": True,
        "limit": 10,
        "days_limit": 14,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/goutongjiaoliu/113456/113469/']",
        ],
        "link_patterns": ["/goutongjiaoliu/113456/113469/"],
        "keywords": [
            "金融市场", "金融统计", "社会融资", "人民币", "货币政策",
            "资本市场", "汇率", "利率", "金融稳定"
        ],
    },
    {
        "name": "人民银行-政策要闻",
        "type": "html_list",
        "url": "https://www.pbc.gov.cn/goutongjiaoliu/index.html",
        "base_url": "https://www.pbc.gov.cn",
        "category": "时政新闻",
        "subcategory": "央行",
        "priority": 94,
        "domestic": True,
        "limit": 8,
        "days_limit": 14,
        "strict_keywords": False,
        "resolve_detail_time": True,
        "resolve_detail_fields": True,
        "link_selectors": [
            "a[href*='/hanglingdao/']",
        ],
        "link_patterns": ["/hanglingdao/"],
        "keywords": [
            "中国人民银行", "行长", "货币政策", "金融稳定", "公告",
            "人民币汇率", "公开市场", "降准", "降息"
        ],
    },
]

CATEGORY_LIMITS = {
    "行业新闻": 20,
    "金融新闻": 8,
    "时政新闻": 18,
    "其他": 4,
}

CATEGORY_MINIMUMS = {
    "行业新闻": 12,
    "金融新闻": 3,
    "时政新闻": 10,
}

PREFERRED_SUBCATEGORY_LIMITS = {
    "基金TA": 10,
    "基金": 10,
    "证券": 2,
    "宏观经济": 4,
    "港股": 1,
    "A股": 1,
    "利率": 2,
    "汇率": 1,
    "民生": 7,
    "社会": 7,
    "国务院": 4,
    "发改委": 3,
    "央行": 2,
    "财政部": 2,
    "证监会": 1,
    "人大": 2,
}

DEFAULT_MAX_ITEMS_PER_SOURCE = 5

SOURCE_LIMITS = {
    "证券时报-首页精选": 4,
    "证券时报-基金": 4,
    "人民银行-新闻发布": 4,
    "财政部-政策发布": 3,
}

SOURCE_FAMILY_LIMITS = {
    "证券时报": 4,
    "财联社": 4,
    "中国证券报": 3,
    "上海证券报": 3,
    "东方财富": 3,
    "21财经": 3,
    "券商中国": 2,
    "基金业协会": 4,
    "中国结算": 4,
    "中国政府网": 5,
    "新华网": 5,
    "中国新闻网": 4,
    "央视网": 4,
    "人民银行": 3,
    "财政部": 2,
    "国家发展改革委": 3,
    "全国人大": 3,
}

PREFERRED_SOURCE_MINIMUMS = {
    "基金业协会-协会要闻": 2,
    "基金业协会-通知公告": 2,
    "中国结算-要闻动态": 2,
    "中国结算-通知公告": 2,
    "中国政府网-要闻速览": 3,
    "新华网-时政民生": 3,
    "中国新闻网-社会民生": 2,
    "央视网-民生观察": 2,
    "东方财富-基金与ETF": 2,
    "21财经-基金发行与资管": 2,
    "上海证券报-基金与配置": 2,
    "上海证券报-宏观与利率": 2,
    "中国证券报-基金快讯": 2,
    "人民银行-新闻发布": 2,
    "人民银行-政策要闻": 1,
}

DOMESTIC_KEYWORDS = [
    "中国", "国内", "国务院", "证监会", "上交所", "深交所", "北交所",
    "港交所", "中国人民银行", "财政部", "全国人大", "A股", "港股",
    "沪指", "深成指", "创业板", "科创板", "基金", "券商"
]

INDUSTRY_PRIORITY_KEYWORDS = [
    "基金", "公募基金", "私募基金", "ETF", "REITs", "基金TA", "基金销售",
    "基金投顾", "基金账户", "份额登记", "登记结算", "清算交收", "托管", "估值"
]

GFFUNDS_FOCUS_KEYWORDS = [
    "公募基金", "基金公司", "基金经理", "ETF", "指数基金", "REITs",
    "资本市场", "资产配置", "机构资金",
    "宏观政策", "财政政策", "货币政策", "中国人民银行", "财政部",
    "LPR", "MLF", "降准", "降息", "社融", "人民币汇率",
    "中国证券投资基金业协会", "基金业协会", "中国证券登记结算", "中国结算",
    "中证登", "基金TA", "TA", "份额登记", "登记结算", "清算交收",
    "基金销售", "销售机构", "代销", "直销", "直销服务平台", "过户",
    "开户", "账户", "投资者服务", "基金E账户", "托管", "估值"
]

GFFUNDS_STRONG_KEYWORDS = [
    "广发基金", "公募基金", "基金经理", "基金投顾", "基金发行", "基金销售",
    "基金申购", "基金赎回", "ETF", "REITs", "QDII", "FOF", "指数增强",
    "股票ETF", "债券ETF", "固收", "可转债",
    "宏观政策", "货币政策", "财政政策", "资本市场", "资产配置",
    "中国证券投资基金业协会", "中国证券登记结算", "中证登", "基金TA",
    "份额登记", "登记结算", "清算交收", "基金销售", "销售机构",
    "直销服务平台", "基金E账户", "过户登记", "基金账户"
]

POLICY_SIGNAL_KEYWORDS = [
    "中国人民银行", "财政部", "国务院", "国务院办公厅", "国家发展改革委", "证监会",
    "金融监管总局", "国新办", "全国人大", "全国人大常委会", "立法", "法律草案",
    "审议", "修订", "工作会议", "政策", "实施意见", "通知", "决定", "公告"
]

CURRENT_AFFAIRS_KEYWORDS = [
    "高温", "降雨", "暴雨", "台风", "强对流", "防汛", "救援", "应急", "医疗",
    "教育", "就业", "消费", "住房", "养老", "社保", "交通", "铁路", "民航",
    "儿童", "家庭病床", "育儿", "食品安全", "春运", "出行", "民生", "社会",
    "医保", "药品", "校园", "反诈", "诈骗", "消防", "地震", "滑坡", "暴雪",
    "沙尘", "空气质量", "生态", "环保", "水质", "城市更新", "公共服务"
]

GFFUNDS_EXCLUDE_KEYWORDS = [
    "娱乐", "明星", "影视", "综艺", "八卦", "体育", "旅游攻略",
    "汽车测评", "美食", "游戏", "动漫", "直播带货"
]

RELEVANCE_SCORE_THRESHOLD = {
    "行业新闻": 14,
    "金融新闻": 9,
    "时政新闻": 3,
    "其他": 99,
}

MORNING_DIGEST_CUTOFF_HOUR = 9
PREFER_PREVIOUS_DAY_IN_MORNING = True
PREVIOUS_DAY_PRIORITY_BOOST = 30
SAME_DAY_EARLY_NEWS_PENALTY = 6

CATEGORY_DISPLAY_ORDER = ["行业新闻", "金融新闻", "时政新闻", "其他"]

SUBCATEGORY_DISPLAY_ORDER = {
    "行业新闻": ["基金TA", "基金", "证券", "A股", "港股"],
    "金融新闻": ["宏观经济", "利率", "汇率", "行情"],
    "时政新闻": ["民生", "社会", "国务院", "发改委", "央行", "财政部", "人大", "证监会"],
}


# ==========================================
# 抓取配置
# ==========================================

# 每个新闻源默认最多抓取的新闻数量
MAX_NEWS_PER_SOURCE = 5

# 总共最多抓取的新闻数量
MAX_TOTAL_NEWS = 40

# 新闻时效性 - 只抓取几天内的新闻 (0表示不过滤)
NEWS_DAYS_LIMIT = 2

# 请求超时时间 (秒)
REQUEST_TIMEOUT = 12

# 请求重试次数
REQUEST_RETRIES = 1

# 请求间隔 (秒) - 避免请求过于频繁
REQUEST_DELAY = 0.15

# 单次抓取流程里，允许做详情页补抓的最大次数，避免因为大量详情页回填导致整体超时
DETAIL_FETCH_BUDGET = 28


# ==========================================
# 定时任务配置
# ==========================================

# 定时运行时间 (24小时制)
SCHEDULE_TIME = time(8, 0)  # 每天早上8:00

# 时区
TIMEZONE = "Asia/Shanghai"


# ==========================================
# 摘要生成配置
# ==========================================

# 摘要最大长度 (字符)
SUMMARY_MAX_LENGTH = 150


# ==========================================
# 日志配置
# ==========================================

# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = "INFO"

# 日志文件路径
LOG_FILE = "news_email_system.log"
