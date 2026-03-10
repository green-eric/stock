#!/usr/bin/env python3
"""
钉钉消息发送工具
支持多种消息类型，适合多Agent炒股系统
"""

import os
import sys
import json
import time
import hashlib
import hmac
import base64
import urllib.parse
from datetime import datetime
from typing import Dict, List, Optional, Union

class DingTalkSender:
    """钉钉消息发送器"""

    def __init__(self, config_file: str = None):
        """
        初始化钉钉发送器

        Args:
            config_file: 配置文件路径，默认为 config/dingtalk.json（相对路径）
        """
        if config_file is None:
            config_file = "config/dingtalk.json"

        self.config_file = config_file
        self.config = self._load_config()
        self.message_queue = []
        self.last_send_time = 0
        self.rate_limit = self.config.get('settings', {}).get('rate_limit', 18)  # 每分钟最多18条

    def _load_config(self) -> Dict:
        """加载配置文件"""
        default_config = {
            "webhook": "",
            "secret": "",
            "at_mobiles": [],
            "enabled": True,
            "settings": {
                "enable_alerts": True,
                "alert_types": ["买入信号", "卖出信号", "止损提醒", "热点推送"],
                "quiet_hours": ["22:00-08:00"],
                "rate_limit": 18
            }
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并配置
                    default_config.update(user_config)
                    return default_config
            except Exception as e:
                print(f"⚠️ 读取配置文件失败 {self.config_file}: {e}", file=sys.stderr)
                return default_config
        else:
            print(f"⚠️ 配置文件不存在 {self.config_file}，使用默认配置", file=sys.stderr)
            return default_config

    def _is_quiet_hour(self) -> bool:
        """检查是否为静默时段"""
        quiet_hours = self.config.get('settings', {}).get('quiet_hours', ["22:00-08:00"])
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        for quiet_range in quiet_hours:
            if '-' in quiet_range:
                start_str, end_str = quiet_range.split('-')
                start = datetime.strptime(start_str, "%H:%M").time()
                end = datetime.strptime(end_str, "%H:%M").time()
                current = now.time()

                if start <= end:
                    if start <= current <= end:
                        return True
                else:
                    # 跨天的情况
                    if current >= start or current <= end:
                        return True
        return False

    def _check_rate_limit(self) -> bool:
        """检查速率限制"""
        current_time = time.time()
        time_diff = current_time - self.last_send_time

        # 每分钟限制
        if time_diff < 60 / self.rate_limit:
            return False
        return True

    def _sign_url(self, webhook: str, secret: str) -> str:
        """生成签名URL"""
        if not secret:
            return webhook

        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        # 添加签名参数
        if '?' in webhook:
            return f"{webhook}&timestamp={timestamp}&sign={sign}"
        else:
            return f"{webhook}?timestamp={timestamp}&sign={sign}"

    def send_message(self,
                    title: str,
                    content: str,
                    msg_type: str = "markdown",
                    level: str = "info",
                    at_mobiles: List[str] = None,
                    is_at_all: bool = False) -> bool:
        """
        发送消息到钉钉

        Args:
            title: 消息标题
            content: 消息内容
            msg_type: 消息类型 (text, markdown, actionCard, feedCard)
            level: 消息级别 (info, warning, error, urgent)
            at_mobiles: @的手机号列表
            is_at_all: 是否@所有人

        Returns:
            bool: 是否发送成功
        """
        # 检查配置
        if not self.config.get('enabled', True):
            print(f"⚠️ 钉钉发送已禁用", file=sys.stderr)
            return False

        webhook = self.config.get('webhook', '')
        if not webhook:
            print(f"❌ 未配置钉钉Webhook", file=sys.stderr)
            return False

        # 检查静默时段
        if self._is_quiet_hour() and level not in ["urgent", "error"]:
            print(f"⏰ 静默时段，消息已保存到队列", file=sys.stderr)
            self.message_queue.append({
                "title": title,
                "content": content,
                "msg_type": msg_type,
                "level": level,
                "timestamp": datetime.now().isoformat()
            })
            return True

        # 检查速率限制
        if not self._check_rate_limit():
            print(f"⏳ 速率限制，消息已保存到队列", file=sys.stderr)
            self.message_queue.append({
                "title": title,
                "content": content,
                "msg_type": msg_type,
                "level": level,
                "timestamp": datetime.now().isoformat()
            })
            return True

        # 准备消息数据
        message_data = {
            "msgtype": msg_type
        }

        # 根据消息类型构造内容
        if msg_type == "text":
            message_data["text"] = {
                "content": f"{title}\n\n{content}"
            }
        elif msg_type == "markdown":
            # 添加级别图标
            level_icons = {
                "info": "🔔",
                "warning": "⚠️",
                "error": "❌",
                "urgent": "🚨"
            }
            icon = level_icons.get(level, "📢")

            message_data["markdown"] = {
                "title": f"{icon} {title}",
                "text": f"### {icon} {title}\n\n{content}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        elif msg_type == "actionCard":
            message_data["actionCard"] = {
                "title": title,
                "text": content,
                "btns": [
                    {
                        "title": "查看详情",
                        "actionURL": "dingtalk://查看详情"
                    }
                ]
            }

        # 添加@信息
        at_list = at_mobiles or self.config.get('at_mobiles', [])
        if at_list or is_at_all:
            message_data["at"] = {
                "atMobiles": at_list,
                "isAtAll": is_at_all
            }

        # 生成签名URL
        secret = self.config.get('secret', '')
        signed_url = self._sign_url(webhook, secret)

        try:
            import requests
            response = requests.post(
                signed_url,
                json=message_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            self.last_send_time = time.time()

            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    print(f"✅ 消息发送成功: {title}", file=sys.stderr)
                    return True
                else:
                    print(f"❌ 钉钉返回错误: {result.get('errmsg')}", file=sys.stderr)
                    return False
            else:
                print(f"❌ HTTP错误: {response.status_code}", file=sys.stderr)
                return False

        except ImportError:
            print(f"❌ 需要安装requests库: pip install requests", file=sys.stderr)
            return False
        except Exception as e:
            print(f"❌ 发送失败: {e}", file=sys.stderr)
            return False

    def send_stock_alert(self,
                        stock_code: str,
                        stock_name: str,
                        alert_type: str,
                        price: float,
                        change_percent: float,
                        reason: str,
                        suggestion: str = "") -> bool:
        """
        发送股票预警消息

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            alert_type: 预警类型 (买入信号, 卖出信号, 止损提醒, 异动预警)
            price: 当前价格
            change_percent: 涨跌幅
            reason: 预警原因
            suggestion: 操作建议

        Returns:
            bool: 是否发送成功
        """
        # 预警级别映射
        alert_levels = {
            "买入信号": "urgent",
            "卖出信号": "error",
            "止损提醒": "warning",
            "异动预警": "info"
        }

        level = alert_levels.get(alert_type, "info")

        # 涨跌幅颜色
        change_color = "🟢" if change_percent > 0 else "🔴"
        change_text = f"{change_color} {change_percent:+.2f}%"

        # 构造消息内容
        content = f"""
**股票**: {stock_code} {stock_name}
**价格**: ¥{price:.2f} {change_text}
**类型**: {alert_type}
**时间**: {datetime.now().strftime('%H:%M:%S')}

**原因**:
{reason}

**建议**:
{suggestion if suggestion else "请及时关注"}

**风控提示**:
- 止损位: 根据个人风险承受能力设置
- 仓位: 建议单只股票≤30%
- 持仓期: 1-3天（超短线）
"""

        title = f"{alert_type}: {stock_code} {stock_name}"

        return self.send_message(
            title=title,
            content=content,
            msg_type="markdown",
            level=level
        )

    def send_market_summary(self,
                           date: str,
                           market_status: str,
                           hot_sectors: List[Dict],
                           top_gainers: List[Dict],
                           top_losers: List[Dict]) -> bool:
        """
        发送市场总结

        Args:
            date: 日期
            market_status: 市场状态 (上涨, 下跌, 震荡)
            hot_sectors: 热点板块列表
            top_gainers: 涨幅榜
            top_losers: 跌幅榜

        Returns:
            bool: 是否发送成功
        """
        # 市场状态图标
        status_icons = {
            "上涨": "📈",
            "下跌": "📉",
            "震荡": "📊"
        }
        icon = status_icons.get(market_status, "📊")

        # 构造热点板块文本
        sectors_text = ""
        for i, sector in enumerate(hot_sectors[:5], 1):
            sectors_text += f"{i}. **{sector.get('name')}**: +{sector.get('change', 0):.1f}%\n"

        # 构造涨幅榜文本
        gainers_text = ""
        for i, stock in enumerate(top_gainers[:3], 1):
            gainers_text += f"{i}. {stock.get('code')} {stock.get('name')}: +{stock.get('change', 0):.2f}%\n"

        content = f"""
**📅 日期**: {date}
**📊 市场状态**: {icon} {market_status}

**🔥 热点板块**:
{sectors_text}

**🚀 涨幅榜**:
{gainers_text}

**💡 操作建议**:
- 关注热点板块轮动
- 控制仓位，分散风险
- 设置止损，严格执行

**⏰ 更新时间**: {datetime.now().strftime('%H:%M:%S')}
"""

        title = f"{icon} 市场总结: {date} {market_status}"

        return self.send_message(
            title=title,
            content=content,
            msg_type="markdown",
            level="info"
        )

    def flush_queue(self) -> bool:
        """发送队列中的消息"""
        if not self.message_queue:
            return True

        print(f"📨 发送队列中的 {len(self.message_queue)} 条消息", file=sys.stderr)

        success_count = 0
        for msg in self.message_queue:
            if self.send_message(
                title=msg["title"],
                content=msg["content"],
                msg_type=msg["msg_type"],
                level=msg["level"]
            ):
                success_count += 1
            time.sleep(3)  # 避免速率限制

        self.message_queue = []
        print(f"✅ 队列发送完成: {success_count}/{len(self.message_queue)} 成功", file=sys.stderr)
        return success_count > 0

def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description='钉钉消息发送工具')
    parser.add_argument('--config', type=str, default='config/dingtalk.json',
                       help='配置文件路径')
    parser.add_argument('--title', type=str, required=True, help='消息标题')
    parser.add_argument('--content', type=str, required=True, help='消息内容')
    parser.add_argument('--type', type=str, default='markdown',
                       choices=['text', 'markdown', 'actionCard'],
                       help='消息类型')
    parser.add_argument('--level', type=str, default='info',
                       choices=['info', 'warning', 'error', 'urgent'],
                       help='消息级别')

    # 股票预警专用参数
    parser.add_argument('--stock-alert', action='store_true',
                       help='发送股票预警消息')
    parser.add_argument('--code', type=str, help='股票代码')
    parser.add_argument('--name', type=str, help='股票名称')
    parser.add_argument('--alert-type', type=str,
                       choices=['买入信号', '卖出信号', '止损提醒', '异动预警'],
                       help='预警类型')
    parser.add_argument('--price', type=float, help='当前价格')
    parser.add_argument('--change', type=float, help='涨跌幅')

    args = parser.parse_args()

    sender = DingTalkSender(args.config)

    if args.stock_alert:
        if not all([args.code, args.name, args.alert_type, args.price, args.change]):
            print("❌ 股票预警需要提供所有参数: --code, --name, --alert-type, --price, --change")
            sys.exit(1)

        success = sender.send_stock_alert(
            stock_code=args.code,
            stock_name=args.name,
            alert_type=args.alert_type,
            price=args.price,
            change_percent=args.change,
            reason="系统自动检测",
            suggestion="请及时处理"
        )
    else:
        success = sender.send_message(
            title=args.title,
            content=args.content,
            msg_type=args.type,
            level=args.level
        )

    if success:
        print("✅ 消息发送成功")
        sys.exit(0)
    else:
        print("❌ 消息发送失败")
        sys.exit(1)

if __name__ == "__main__":
    main()