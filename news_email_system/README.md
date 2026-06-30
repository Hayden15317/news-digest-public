# 自动新闻邮件推送系统

一个基于 Python 的自动化新闻抓取和邮件推送系统，支持 RSS 新闻源、智能分类、摘要生成和邮件推送。

## 功能特点

- **RSS 新闻抓取**：支持多个 RSS 源同时抓取
- **智能分类**：自动将新闻分类到行业、金融、时政等类别
- **摘要生成**：自动为新闻生成简短摘要
- **HTML 邮件**：生成美观的 HTML 格式邮件
- **定时推送**：支持定时任务（如每天早上8点）
- **模块化设计**：抓取、分类、邮件发送独立模块

## 新闻分类

### 行业新闻
- **证券**：IPO、股市、券商、交易所等
- **基金**：公募基金、私募基金、ETF 等
- **A股**：上证指数、沪深300、创业板等
- **港股**：恒生指数、港股通等

### 金融新闻
- **行情**：技术分析、K线、成交量等
- **宏观经济**：GDP、CPI、PMI 等
- **利率**：LPR、MLF、货币政策等
- **汇率**：人民币汇率、美元指数等

### 时政新闻
- **央行**：中国人民银行、美联储等
- **财政部**：财政政策、国债、预算等
- **人大**：立法、审议、政府工作报告等

## 项目结构

```
news_email_system/
├── config.py           # 配置文件
├── fetcher.py          # 新闻抓取模块
├── classifier.py       # 新闻分类模块
├── summarizer.py       # 摘要生成模块
├── sender.py           # 邮件发送模块
├── main.py             # 主程序入口
├── requirements.txt    # 依赖包列表
└── README.md           # 项目说明文档
```

## 安装步骤

### 1. 克隆或下载项目

```bash
cd news_email_system
```

### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置邮件参数

编辑 `config.py` 文件，配置邮件发送参数：

```python
# SMTP服务器配置（以QQ邮箱为例）
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USE_SSL = True

# 发件人配置
SENDER_EMAIL = "your_email@qq.com"      # 发件人邮箱
SENDER_PASSWORD = "your_auth_code"       # 邮箱授权码（非密码）
SENDER_NAME = "新闻推送助手"              # 发件人显示名称

# 收件人配置
RECIPIENT_EMAILS = ["recipient@example.com"]  # 收件人邮箱列表
```

#### 获取邮箱授权码

**QQ邮箱：**
1. 登录QQ邮箱网页版
2. 点击"设置" -> "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 开启"SMTP服务"，获取授权码

**163邮箱：**
1. 登录163邮箱网页版
2. 点击"设置" -> "POP3/SMTP/IMAP"
3. 开启SMTP服务，获取授权码

### 5. 配置RSS源（可选）

编辑 `config.py` 文件中的 `RSS_SOURCES` 变量，添加或修改RSS源：

```python
RSS_SOURCES = {
    "行业新闻": {
        "证券": [
            "https://example.com/rss/finance",
        ],
        # ...
    },
}
```

## 使用说明

### 1. 立即运行一次

```bash
python main.py --once
```

### 2. 启动定时任务（每天早上8点运行）

```bash
python main.py
```

按 `Ctrl+C` 停止程序。

### 3. 测试模式（只抓取新闻，不发送邮件）

```bash
python main.py --test
```

### 4. 查看帮助

```bash
python main.py --help
```

## 部署方案

### 方案1：本地电脑运行

适合个人使用，需要保持电脑开机。

1. 按照安装步骤配置好环境
2. 运行 `python main.py` 启动定时任务
3. 保持程序运行（可以最小化到托盘）

### 方案2：服务器部署（推荐）

适合长期稳定运行。

**使用 systemd（Linux）：**

1. 创建服务文件 `/etc/systemd/system/news-email.service`：

```ini
[Unit]
Description=News Email System
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/news_email_system
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. 启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable news-email
sudo systemctl start news-email
```

3. 查看状态：

```bash
sudo systemctl status news-email
sudo journalctl -u news-email -f
```

**使用 Docker：**

1. 创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

2. 创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  news-email:
    build: .
    container_name: news-email-system
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    environment:
      - TZ=Asia/Shanghai
```

3. 运行：

```bash
docker-compose up -d
```

## 常见问题

### 1. 邮件发送失败

**问题：** 提示 "SMTP Authentication Error" 或 "535 Error"

**解决方案：**
- 检查邮箱地址和授权码是否正确
- 确保开启了SMTP服务
- 检查SMTP服务器地址和端口是否正确
- 对于QQ邮箱，使用授权码而不是登录密码

### 2. 抓取不到新闻

**问题：** 运行程序后显示 "没有抓取到任何新闻"

**解决方案：**
- 检查网络连接
- 检查RSS源地址是否有效（可以在浏览器中打开测试）
- 尝试更换其他RSS源
- 检查 `config.py` 中的 `NEWS_DAYS_LIMIT` 设置

### 3. 定时任务不运行

**问题：** 程序运行正常，但到设定时间不执行

**解决方案：**
- 检查时区设置是否正确（`TIMEZONE` 应为 "Asia/Shanghai"）
- 检查系统时间是否正确
- 查看日志文件了解错误信息

### 4. 邮件进入垃圾箱

**问题：** 发送的邮件被接收方邮箱标记为垃圾邮件

**解决方案：**
- 使用企业邮箱或域名邮箱（比免费邮箱更可信）
- 添加SPF、DKIM、DMARC记录（需要域名控制）
- 优化邮件内容，避免使用敏感词汇
- 提醒收件人将发件人添加到通讯录

## 更新日志

### v1.0.0 (2026-06-22)
- 初始版本发布
- 支持RSS新闻抓取
- 支持新闻智能分类
- 支持自动生成摘要
- 支持HTML邮件发送
- 支持定时任务调度

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 发送邮件至：your_email@example.com

---

**感谢使用自动新闻邮件推送系统！**
