#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钉钉通知模块 - 多Agent炒股系统
支持钉钉机器人Webhook消息推送
"""

import json
import time
import hmac
import hashlib
import base64
import logging
import sys
from typing import Dict, Optional, Any
from urllib.parse import urlencode, quote

# 尝试导入requests，如果不可用则使用urllib回退
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False
    print("警告: requests模块不可用，将使用urllib作为HTTP客户端")

logger = logging.getLogger(__name__)


class DingTalkNotifier:
    """钉钉机器人通知器"""

    def __init__(self, webhook_url: str, secret: str = None):
        """
        初始化钉钉通知器

        Args:
            webhook_url: 钉钉机器人Webhook URL
            secret: 加签密钥（可选）
        """
        self.webhook_url = webhook_url.rstrip('&')
        self.secret = secret
        self.logger = logging.getLogger(__name__)

    def _build_webhook_url(self) -> str:
        """构建带签名的Webhook URL"""
        if not self.secret:
            return self.webhook_url

        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.secret}"

        # HMAC-SHA256签名
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()

        sign = base64.b64encode(hmac_code).decode('utf-8')
        # 钉钉要求对base64签名进行URL编码，而不是URL安全替换
        sign_encoded = quote(sign, safe='')
        timestamp_encoded = quote(timestamp, safe='')

        return f"{self.webhook_url}&timestamp={timestamp_encoded}&sign={sign_encoded}"

    def _send_message(self, message: Dict) -> Dict:
        """
        发送消息到钉钉

        Args:
            message: 消息内容字典

        Returns:
            钉钉API响应
        """
        webhook_url = self._build_webhook_url()

        headers = {
            "Content-Type": "application/json",
            "Charset": "UTF-8"
        }

        data = json.dumps(message, ensure_ascii=False).encode('utf-8')

        try:
            self.logger.info(f"发送钉钉消息: {json.dumps(message, ensure_ascii=False)[:100]}...")

            if HAS_REQUESTS:
                # 使用requests库
                response = requests.post(
                    webhook_url,
                    headers=headers,
                    data=data,
                    timeout=10
                )
                result = response.json()
            else:
                # 使用urllib回退
                req = urllib.request.Request(
                    webhook_url,
                    data=data,
                    headers=headers,
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    response_data = response.read().decode('utf-8')
                    result = json.loads(response_data)

            if result.get("errcode") == 0:
                self.logger.info(f"钉钉消息发送成功: {result}")
            else:
                self.logger.error(f"钉钉消息发送失败: {result}")

            return result

        except Exception as e:
            self.logger.error(f"钉钉请求异常: {e}")
            return {"errcode": -1, "errmsg": str(e)}

    def send_text(self, content: str, at_all: bool = False, at_mobiles: list = None) -> Dict:
        """
        发送文本消息

        Args:
            content: 消息内容
            at_all: 是否@所有人
            at_mobiles: 要@的手机号列表

        Returns:
            钉钉API响应
        """
        message = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }

        if at_all or at_mobiles:
            message["at"] = {}
            if at_all:
                message["at"]["isAtAll"] = True
            if at_mobiles:
                message["at"]["atMobiles"] = at_mobiles

        return self._send_message(message)

    def send_markdown(self, title: str, text: str, at_all: bool = False, at_mobiles: list = None) -> Dict:
        """
        发送Markdown消息

        Args:
            title: 标题
            text: Markdown内容
            at_all: 是否@所有人
            at_mobiles: 要@的手机号列表

        Returns:
            钉钉API响应
        """
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            }
        }

        if at_all or at_mobiles:
            message["at"] = {}
            if at_all:
                message["at"]["isAtAll"] = True
            if at_mobiles:
                message["at"]["atMobiles"] = at_mobiles

        return self._send_message(message)

    def test_connection(self) -> bool:
        """测试钉钉连接"""
        test_msg = "🔌 钉钉连接测试 - 多Agent炒股系统通知测试"
        result = self.send_text(test_msg)

        if result.get("errcode") == 0:
            self.logger.info("钉钉连接测试成功")
            return True
        else:
            self.logger.error(f"钉钉连接测试失败: {result}")
            return False


# 全局通知器实例
_notifier_instance = None


def init_notifier(config_path: str = "config/dingtalk.json") -> Optional[DingTalkNotifier]:
    """
    初始化钉钉通知器

    Args:
        config_path: 配置文件路径

    Returns:
        钉钉通知器实例或None
    """
    global _notifier_instance

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if not config.get("enabled", False):
            logger.info("钉钉通知已禁用")
            return None

        webhook_url = config.get("webhook", "")
        secret = config.get("secret", "")

        if not webhook_url:
            logger.warning("钉钉Webhook URL未配置")
            return None

        _notifier_instance = DingTalkNotifier(webhook_url, secret)
        logger.info("钉钉通知器初始化成功")
        return _notifier_instance

    except FileNotFoundError:
        logger.warning(f"钉钉配置文件不存在: {config_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"钉钉配置文件解析失败: {e}")
        return None
    except Exception as e:
        logger.error(f"钉钉通知器初始化失败: {e}")
        return None


def get_notifier() -> Optional[DingTalkNotifier]:
    """获取钉钉通知器实例"""
    return _notifier_instance


def notify_agent_event(agent_name: str, event_type: str, message: str = "", extra_data: Dict = None) -> bool:
    """
    发送Agent事件通知

    Args:
        agent_name: Agent名称
        event_type: 事件类型 (start/stop/error)
        message: 附加消息
        extra_data: 额外数据

    Returns:
        是否发送成功
    """
    notifier = get_notifier()
    if not notifier:
        return False

    event_map = {
        "start": "🚀 Agent启动",
        "stop": "🛑 Agent停止",
        "error": "❌ Agent异常"
    }

    event_title = event_map.get(event_type, f"Agent事件: {event_type}")

    content = f"**{event_title}**\n\n"
    content += f"**Agent**: {agent_name}\n"
    content += f"**时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"

    if message:
        content += f"**消息**: {message}\n"

    if extra_data:
        content += "**详情**:\n"
        for key, value in extra_data.items():
            content += f"- {key}: {value}\n"

    result = notifier.send_markdown(f"{event_title} - {agent_name}", content)
    return result.get("errcode") == 0


def notify_system_alert(alert_type: str, severity: str, message: str, details: Dict = None) -> bool:
    """
    发送系统告警通知

    Args:
        alert_type: 告警类型
        severity: 严重程度 (info/warning/error/critical)
        message: 告警消息
        details: 详细数据

    Returns:
        是否发送成功
    """
    notifier = get_notifier()
    if not notifier:
        return False

    severity_map = {
        "info": "ℹ️ 信息",
        "warning": "⚠️ 警告",
        "error": "❌ 错误",
        "critical": "🚨 严重"
    }

    severity_title = severity_map.get(severity, severity)

    content = f"**{severity_title} - {alert_type}**\n\n"
    content += f"**消息**: {message}\n"
    content += f"**时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"

    if details:
        content += "**详情**:\n"
        for key, value in details.items():
            content += f"- {key}: {value}\n"

    result = notifier.send_markdown(f"{severity_title} - {alert_type}", content)
    return result.get("errcode") == 0


if __name__ == "__main__":
    # 测试代码
    import argparse

    parser = argparse.ArgumentParser(description="钉钉通知器测试")
    parser.add_argument("--test", action="store_true", help="测试钉钉连接")
    parser.add_argument("--config", default="config/dingtalk.json", help="配置文件路径")
    args = parser.parse_args()

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if args.test:
        notifier = init_notifier(args.config)
        if notifier:
            success = notifier.test_connection()
            sys.exit(0 if success else 1)
        else:
            logger.error("钉钉通知器初始化失败")
            sys.exit(1)
    else:
        print("使用 --test 参数测试钉钉连接")