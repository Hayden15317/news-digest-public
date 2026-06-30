# GitHub Pages 接入说明

## 目标

把邮件顶部的“立即查看”跳转到公网晨报页面，例如：

```text
https://<github-username>.github.io/<repo-name>/reports/latest.html#industry-news
```

## 当前代码已完成的事

- `news_email_system/sender.py`
  - 支持将顶部卡片链接切到公网晨报页面
  - 支持导出 `reports/latest.html` 和 `reports/<user_id>.html`
- `news_email_system/main.py`
  - 每次测试预览或正式发送时自动刷新晨报网页
- `.github/workflows/deploy-github-pages.yml`
  - 当仓库推送到 `main` 分支后，自动发布 `index.html` 和 `reports/` 到 GitHub Pages

## 你需要做的事

1. 安装 Git，并确保命令行能执行 `git --version`
2. 在 GitHub 新建仓库，例如 `news-digest-public`
3. 把当前项目作为 Git 仓库推送到 GitHub
4. 在仓库设置中开启 GitHub Pages
5. 配置公网地址到环境变量 `PUBLIC_REPORT_SITE_URL`

## 推荐公网地址格式

如果你的 GitHub 用户名是 `yourname`，仓库名是 `news-digest-public`，那么公网地址通常是：

```text
https://yourname.github.io/news-digest-public
```

此时请把：

```text
PUBLIC_REPORT_SITE_URL=https://yourname.github.io/news-digest-public
```

写入系统环境变量，或在启动前临时设置。

## Windows 临时设置方式

在 PowerShell 中执行：

```powershell
$env:PUBLIC_REPORT_SITE_URL="https://yourname.github.io/news-digest-public"
python main.py --test --user-config users.json
```

## 长期生效方式

可以把这行加入你自己的启动脚本，或者在系统环境变量里新增：

```text
PUBLIC_REPORT_SITE_URL
```

值为：

```text
https://yourname.github.io/news-digest-public
```

## 首次上传仓库示例

```powershell
git init
git branch -M main
git add .
git commit -m "init github pages publish"
git remote add origin https://github.com/<github-username>/<repo-name>.git
git push -u origin main
```

## GitHub Pages 设置

进入仓库：

`Settings` -> `Pages` -> `Build and deployment`

选择：

- `Source`: `GitHub Actions`

保存后，只要你后续推送 `reports/` 更新，GitHub Pages 就会自动刷新公网网页。

## 如何验证

推送完成后，先打开：

```text
https://<github-username>.github.io/<repo-name>/reports/latest.html
```

如果页面正常，再测试栏目锚点：

```text
https://<github-username>.github.io/<repo-name>/reports/latest.html#industry-news
```

## 说明

- 邮件顶部卡片只有在 `PUBLIC_REPORT_SITE_URL` 已配置时，才会跳公网网页
- 未配置时，会退回到邮件内部锚点
- `reports/latest.html` 适合通用链接
- `reports/<user_id>.html` 适合不同用户独立晨报版本
