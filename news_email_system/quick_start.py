"""
快速启动脚本 - 自动新闻邮件推送系统

这个脚本提供一个简单的交互式界面，帮助用户快速配置和启动系统。
"""

import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.py')


def print_header():
    """打印标题"""
    print("=" * 60)
    print("   自动新闻邮件推送系统 - 快速启动")
    print("=" * 60)
    print()


def get_email_config():
    """获取邮箱配置"""
    print("📧 第一步：配置邮箱")
    print("-" * 60)
    print("提示：请使用QQ邮箱或163邮箱")
    print("注意：需要开启SMTP服务并获取授权码")
    print()

    # 选择邮箱类型
    while True:
        email_type = input("请选择邮箱类型 [1:QQ邮箱 2:163邮箱]: ").strip()
        if email_type in ['1', '2']:
            break
        print("❌ 无效的选择，请重新输入")

    if email_type == '1':
        smtp_server = "smtp.qq.com"
        smtp_port = "465"
        default_email_suffix = "@qq.com"
    else:
        smtp_server = "smtp.163.com"
        smtp_port = "465"
        default_email_suffix = "@163.com"

    # 发件人邮箱
    while True:
        sender_email = input(f"请输入发件人邮箱 [{default_email_suffix}]: ").strip()
        if not sender_email:
            print("❌ 邮箱不能为空")
            continue
        if '@' not in sender_email:
            sender_email += default_email_suffix
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', sender_email):
            break
        print("❌ 邮箱格式不正确，请重新输入")

    # 授权码
    while True:
        auth_code = input("请输入邮箱授权码（不是登录密码）: ").strip()
        if auth_code:
            break
        print("❌ 授权码不能为空")

    # 收件人邮箱
    while True:
        recipient_emails = input("请输入收件人邮箱（多个用逗号分隔）: ").strip()
        if not recipient_emails:
            print("❌ 收件人邮箱不能为空")
            continue

        emails = [e.strip() for e in recipient_emails.split(',')]
        valid = True
        for email in emails:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                print(f"❌ 邮箱格式不正确: {email}")
                valid = False
                break

        if valid:
            recipient_emails = ', '.join(emails)
            break

    return {
        'smtp_server': smtp_server,
        'smtp_port': smtp_port,
        'sender_email': sender_email,
        'auth_code': auth_code,
        'recipient_emails': recipient_emails
    }


def save_config(config):
    """保存配置到文件"""
    config_content = f'''# 自动生成的配置文件
# 生成时间: {__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# 邮件服务器配置
SMTP_SERVER = "{config['smtp_server']}"
SMTP_PORT = {config['smtp_port']}
SMTP_USE_SSL = True

# 发件人配置
SENDER_EMAIL = "{config['sender_email']}"
SENDER_PASSWORD = "{config['auth_code']}"
SENDER_NAME = "新闻推送助手"

# 收件人配置
RECIPIENT_EMAILS = "{config['recipient_emails']}".split(",")
'''

    # 备份原配置
    if os.path.exists(CONFIG_FILE):
        backup_name = os.path.join(
            BASE_DIR,
            f"config.py.backup.{__import__('datetime').datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(backup_name, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 原配置已备份到: {os.path.basename(backup_name)}")
        except Exception as e:
            print(f"⚠️ 备份配置时出错: {e}")

    # 保存新配置
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(config_content)

    print(f"✅ 配置已保存到: {CONFIG_FILE}")


def test_connection(config):
    """测试邮件连接"""
    print("\n📧 测试邮件发送...")
    print("-" * 60)

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header

        # 连接服务器
        print("1. 连接SMTP服务器...")
        server = smtplib.SMTP_SSL(config['smtp_server'], int(config['smtp_port']))
        print("   ✅ 连接成功")

        # 登录
        print("2. 登录邮箱...")
        server.login(config['sender_email'], config['auth_code'])
        print("   ✅ 登录成功")

        # 发送测试邮件
        print("3. 发送测试邮件...")
        msg = MIMEText("这是一封测试邮件，如果您收到此邮件，说明配置正确！", 'plain', 'utf-8')
        msg['Subject'] = Header('测试邮件 - 新闻推送系统', 'utf-8')
        msg['From'] = config['sender_email']
        msg['To'] = config['recipient_emails']

        server.sendmail(
            config['sender_email'],
            config['recipient_emails'].split(','),
            msg.as_string()
        )
        print("   ✅ 测试邮件发送成功")

        # 断开连接
        server.quit()

        print("-" * 60)
        print("✅ 所有测试通过！配置正确。")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        print("\n常见错误及解决方案：")
        print("1. 535错误 - 授权码错误或SMTP服务未开启")
        print("2. 550错误 - 邮箱地址不存在或被拒绝")
        print("3. 连接超时 - 网络问题或服务器地址错误")
        return False


def main():
    """主函数"""
    print_header()

    print("欢迎使用自动新闻邮件推送系统！")
    print()
    print("本向导将帮助您：")
    print("  1. 配置邮箱信息")
    print("  2. 测试邮件发送")
    print("  3. 启动新闻推送系统")
    print()
    print("-" * 60)

    # 获取配置
    config = get_email_config()

    # 确认信息
    print("\n" + "=" * 60)
    print("配置信息确认")
    print("=" * 60)
    print(f"SMTP服务器: {config['smtp_server']}")
    print(f"SMTP端口: {config['smtp_port']}")
    print(f"发件人邮箱: {config['sender_email']}")
    print(f"收件人邮箱: {config['recipient_emails']}")
    print("=" * 60)

    confirm = input("\n信息是否正确？ [Y/n]: ").strip().lower()
    if confirm in ['n', 'no', '否']:
        print("\n已取消，请重新运行向导。")
        return

    # 保存配置
    print("\n💾 保存配置...")
    save_config(config)

    # 测试连接
    test_passed = test_connection(config)

    if test_passed:
        print("\n" + "=" * 60)
        print("🎉 配置完成！")
        print("=" * 60)
        print()
        print("您现在可以：")
        print()
        print("  1. 立即测试运行一次：")
        print("     python main.py --once")
        print()
        print("  2. 启动定时调度（每天早上8点）：")
        print("     python main.py")
        print()
        print("  3. 仅测试抓取（不发送邮件）：")
        print("     python main.py --test")
        print()
        print("=" * 60)

        # 询问是否立即运行
        run_now = input("\n是否立即运行一次测试？ [Y/n]: ").strip().lower()
        if run_now not in ['n', 'no', '否']:
            print("\n🚀 启动系统...\n")
            os.system(f'{sys.executable} main.py --once')

    else:
        print("\n" + "=" * 60)
        print("⚠️ 测试未通过")
        print("=" * 60)
        print()
        print("请检查以下配置：")
        print("  1. 邮箱地址是否正确")
        print("  2. 授权码是否正确（不是登录密码）")
        print("  3. 是否开启了SMTP服务")
        print()
        print("您可以：")
        print("  - 重新运行本向导: python quick_start.py")
        print("  - 手动编辑配置文件: config.py")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
