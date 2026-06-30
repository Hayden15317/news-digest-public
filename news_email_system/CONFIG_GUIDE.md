# 可配置系统说明

## 配置入口

- 默认共享发件 SMTP 由 `news_email_system/config.py` 管理。
- 多用户收件与偏好由 `news_email_system/users.json` 管理。
- 可复用团队模板见 `news_email_system/users.team.template.json`。
- 如果只是新增使用人，不需要改 SMTP，只需要在 `users.json` 里新增一个用户对象。
- 如果某个使用人想单独指定自己的发件邮箱，也可以在该用户对象里填 `smtp_server`、`smtp_port`、`smtp_use_ssl`、`sender_email`、`sender_password`。

## 常用字段

- `user_id`: 用户唯一标识，用于命令行指定单个用户。
- `enabled`: 是否启用该用户。
- `smtp_server`: 可选，单个用户自己的 SMTP 服务器；留空则沿用系统共享 SMTP。
- `smtp_port`: 可选，单个用户自己的 SMTP 端口。
- `smtp_use_ssl`: 可选，单个用户是否启用 SSL，可填 `true` / `false`。
- `sender_email`: 可选，单个用户自己的发件邮箱。
- `sender_password`: 可选，单个用户自己的授权码或 SMTP 密码。
- `recipient_emails`: 收件人列表。
- `reply_to`: 回复地址，可留空。
- `subject_prefix`: 邮件标题前缀。
- `send_time`: 发送时间，例如 `08:00`。
- `timezone`: 时区，默认 `Asia/Shanghai`。
- `preferences.categories`: 主分类偏好。
- `preferences.subcategories`: 子分类偏好。
- `preferences.include_keywords`: 必须尽量命中的关键词。
- `preferences.exclude_keywords`: 需要排除的关键词。
- `preferences.max_items`: 该用户最多接收多少条新闻。

## 常用命令

```bash
python main.py --test --user-config users.json
python main.py --test --user-config users.json --user default-self-test
python main.py --once --user-config users.json
python main.py
```

## 新增一个使用人

1. 复制 `users.json` 里的一个用户对象。
2. 修改 `user_id`、`name`、`recipient_emails`。
3. 按需要修改 `send_time` 和 `preferences`。
4. 如果要共用系统发件账号，保持 `smtp_*` 和 `sender_email` / `sender_password` 为空即可。
5. 如果要单独指定发件账号，填入该用户自己的 SMTP 参数。
6. 把 `enabled` 改成 `true`。

## 复用团队模板

1. 把 `users.team.template.json` 复制为新的 `users.json`，或者把其中一个用户对象复制到现有 `users.json`。
2. 修改 `recipient_emails` 为团队邮箱或目标收件人。
3. 修改 `reply_to` 为实际负责人邮箱。
4. 把要启用的模板对象 `enabled` 改成 `true`。
5. 用 `python main.py --test --user-config users.json` 先预览，再正式发送。

## 注意

- 根目录的 `config.py` 是历史快速配置文件，不再作为多人配置入口。
- 如果只是改收件人或偏好，优先改 `news_email_system/users.json`。
