"""
本地网页控制服务。

用途：
1. 提供固定本地网页入口
2. 接收网页提交的 users.json 配置
3. 触发测试预览或正式发送流程
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional


HOST = "127.0.0.1"
PORT = 8765
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_WEB_USERS_PATH = os.path.join(PROJECT_DIR, "users.web.json")
HTML_ENTRY_PATH = os.path.join(PROJECT_DIR, "team_configurator.html")
LOCAL_REPORTS_DIR = os.path.join(PROJECT_DIR, "reports")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
BUILD_VERSION = "2026-06-29-1442"

_send_lock = threading.Lock()


def _normalize_email_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text:
            result.append(text)
    return result


def _has_placeholder_email(values: list[str]) -> bool:
    for value in values:
        normalized = value.strip().lower()
        if normalized.endswith("@example.com") or normalized.endswith("@example.org") or normalized.endswith("@example.net"):
            return True
    return False


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
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    return None


def _validate_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(payload.get("user_id", "")).strip()
    name = str(payload.get("name", "")).strip()
    recipient_emails = _normalize_email_list(payload.get("recipient_emails"))

    if not user_id:
        raise ValueError("user_id 不能为空")
    if not name:
        raise ValueError("name 不能为空")
    if not recipient_emails:
        raise ValueError("recipient_emails 至少需要一个邮箱")

    preferences = payload.get("preferences") or {}
    if not isinstance(preferences, dict):
        preferences = {}

    max_items = preferences.get("max_items", 20)
    try:
        max_items = max(1, int(max_items))
    except (TypeError, ValueError):
        max_items = 20

    return {
        "user_id": user_id,
        "name": name,
        "enabled": True,
        "smtp_server": str(payload.get("smtp_server", "")).strip(),
        "smtp_port": _parse_optional_int(payload.get("smtp_port")),
        "smtp_use_ssl": _parse_optional_bool(payload.get("smtp_use_ssl")),
        "sender_email": str(payload.get("sender_email", "")).strip(),
        "sender_password": str(payload.get("sender_password", "")).strip(),
        "recipient_emails": recipient_emails,
        "sender_name": str(payload.get("sender_name", "新闻推送助手")).strip() or "新闻推送助手",
        "reply_to": str(payload.get("reply_to", "")).strip(),
        "subject_prefix": str(payload.get("subject_prefix", "【广发基金视角晨报】")).strip() or "【广发基金视角晨报】",
        "send_time": str(payload.get("send_time", "08:00")).strip() or "08:00",
        "timezone": str(payload.get("timezone", "Asia/Shanghai")).strip() or "Asia/Shanghai",
        "preferences": {
            "categories": [str(item).strip() for item in preferences.get("categories", []) if str(item).strip()],
            "subcategories": [str(item).strip() for item in preferences.get("subcategories", []) if str(item).strip()],
            "include_keywords": [str(item).strip() for item in preferences.get("include_keywords", []) if str(item).strip()],
            "exclude_keywords": [str(item).strip() for item in preferences.get("exclude_keywords", []) if str(item).strip()],
            "max_items": max_items,
            "min_relevance_score": int(preferences.get("min_relevance_score", 0) or 0),
            "send_empty_email": bool(preferences.get("send_empty_email", False)),
        },
    }


def _write_temp_users_file(profile_payload: Dict[str, Any]) -> str:
    wrapped = {"users": [profile_payload]}
    with open(TEMP_WEB_USERS_PATH, "w", encoding="utf-8") as file:
        json.dump(wrapped, file, ensure_ascii=False, indent=2)
    return TEMP_WEB_USERS_PATH


def _merge_process_output(stdout: Any, stderr: Any) -> str:
    stdout_text = (stdout or "") if isinstance(stdout, str) else ""
    stderr_text = (stderr or "") if isinstance(stderr, str) else ""
    return (stdout_text + ("\n" + stderr_text if stderr_text else "")).strip()


def _infer_stage_from_output(output: str, send_mode: str) -> str:
    text = output or ""
    stage_mapping = [
        ("步骤 1/4: 抓取新闻", "抓取新闻"),
        ("步骤 2/4: 分类新闻", "分类新闻"),
        ("步骤 3/4: 生成摘要", "生成摘要"),
        ("步骤 4/4: 按用户配置发送邮件", "按用户配置发送邮件"),
    ]
    last_stage = "初始化请求"
    for marker, label in stage_mapping:
        if marker in text:
            last_stage = label

    if send_mode == "preview" and "命中新闻数:" in text:
        return "预览结果整理"
    if send_mode == "send" and "准备发送" in text:
        return "SMTP 发送"
    return last_stage


def _run_python_flow(user_config_path: str, user_id: str, send_mode: str) -> Dict[str, Any]:
    if send_mode == "preview":
        command = [
            sys.executable,
            "main.py",
            "--test",
            "--user-config",
            user_config_path,
            "--user",
            user_id,
        ]
    else:
        command = [
            sys.executable,
            "main.py",
            "--once",
            "--user-config",
            user_config_path,
            "--user",
            user_id,
        ]

    logger.info("开始执行网页请求(%s): %s", send_mode, " ".join(command))
    started_at = time.monotonic()
    env = os.environ.copy()
    # Force UTF-8 for the child process so browser logs do not show mojibake on Windows.
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    completed = subprocess.run(
        command,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=600,
    )
    duration_seconds = round(time.monotonic() - started_at, 2)
    output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    return {
        "success": completed.returncode == 0,
        "exit_code": completed.returncode,
        "duration_seconds": duration_seconds,
        "command": " ".join(command),
        "output": output.strip(),
        "stage": _infer_stage_from_output(output, send_mode),
    }


class WebControlHandler(BaseHTTPRequestHandler):
    server_version = "NewsEmailWebControl/1.0"

    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        if self.path in {"/", "/team_configurator.html"}:
            self._send_html_file(HTML_ENTRY_PATH)
            return

        if self.path.startswith("/reports/"):
            self._send_report_file(self.path)
            return

        if self.path == "/api/health":
            self._send_json(
                {
                    "ok": True,
                    "host": HOST,
                    "port": PORT,
                    "build_version": BUILD_VERSION,
                    "project_dir": PROJECT_DIR,
                    "temp_user_config": TEMP_WEB_USERS_PATH,
                    "local_report_base": f"http://{HOST}:{PORT}/reports/",
                }
            )
            return

        self._send_json({"ok": False, "message": "未找到接口"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path not in {"/api/test-preview", "/api/send-now"}:
            self._send_json({"ok": False, "message": "未找到接口"}, status=HTTPStatus.NOT_FOUND)
            return

        send_mode = "preview" if self.path == "/api/test-preview" else "send"

        if not _send_lock.acquire(blocking=False):
            self._send_json(
                {"ok": False, "message": "当前已有发送任务在执行，请稍后再试"},
                status=HTTPStatus.CONFLICT,
            )
            return

        try:
            payload = self._read_json_body()
            profile_payload = _validate_payload(payload)

            if send_mode == "send" and _has_placeholder_email(profile_payload["recipient_emails"]):
                self._send_json(
                    {
                        "ok": False,
                        "message": "正式发送已拦截：收件人仍是模板占位邮箱，请先改成真实邮箱再发送",
                    },
                    status=HTTPStatus.BAD_REQUEST,
                )
                return

            user_config_path = _write_temp_users_file(profile_payload)
            result = _run_python_flow(user_config_path, profile_payload["user_id"], send_mode)

            response = {
                "ok": result["success"],
                "message": self._build_success_message(send_mode, result["success"]),
                "user_config_path": user_config_path,
                "exit_code": result["exit_code"],
                "duration_seconds": result["duration_seconds"],
                "command": result["command"],
                "send_mode": send_mode,
                "stage": result.get("stage", ""),
                "output": result["output"],
            }
            status = HTTPStatus.OK if result["success"] else HTTPStatus.INTERNAL_SERVER_ERROR
            self._send_json(response, status=status)
        except subprocess.TimeoutExpired as error:
            output = _merge_process_output(error.stdout, error.stderr)
            stage = _infer_stage_from_output(output, send_mode)
            duration_seconds = round(float(getattr(error, "timeout", 0) or 0), 2)
            mode_label = "测试预览" if send_mode == "preview" else "正式发送"
            self._send_json(
                {
                    "ok": False,
                    "message": f"{mode_label}超时，当前卡在“{stage}”阶段",
                    "send_mode": send_mode,
                    "stage": stage,
                    "duration_seconds": duration_seconds,
                    "exit_code": None,
                    "command": "",
                    "output": output,
                },
                status=HTTPStatus.GATEWAY_TIMEOUT,
            )
        except ValueError as error:
            self._send_json(
                {"ok": False, "message": str(error)},
                status=HTTPStatus.BAD_REQUEST,
            )
        except Exception as error:  # pragma: no cover - 兜底日志
            logger.exception("网页测试发送失败: %s", error)
            self._send_json(
                {"ok": False, "message": f"服务异常: {error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        finally:
            _send_lock.release()

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length).decode("utf-8")
        payload = json.loads(raw_body or "{}")
        if not isinstance(payload, dict):
            raise ValueError("请求体必须是 JSON 对象")
        return payload

    def _send_json(self, payload: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_html_file(self, file_path: str) -> None:
        if not os.path.exists(file_path):
            self._send_json({"ok": False, "message": "网页文件不存在"}, status=HTTPStatus.NOT_FOUND)
            return

        with open(file_path, "rb") as file:
            body = file.read()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(body)

    def _send_report_file(self, request_path: str) -> None:
        relative_path = request_path.split("?", 1)[0].lstrip("/")
        normalized = os.path.normpath(relative_path)
        file_path = os.path.normpath(os.path.join(PROJECT_DIR, normalized))
        reports_root = os.path.normpath(LOCAL_REPORTS_DIR)

        if not file_path.startswith(reports_root):
            self._send_json({"ok": False, "message": "非法报告路径"}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_html_file(file_path)

    def _build_success_message(self, send_mode: str, success: bool) -> str:
        if send_mode == "preview":
            return "测试预览成功" if success else "测试预览失败"
        return "正式发送成功" if success else "正式发送失败"

    def log_message(self, format: str, *args: Any) -> None:
        logger.info("%s - %s", self.address_string(), format % args)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), WebControlHandler)
    logger.info("网页控制服务已启动: http://%s:%s", HOST, PORT)
    logger.info("固定网页地址: http://%s:%s/", HOST, PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭网页控制服务")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
