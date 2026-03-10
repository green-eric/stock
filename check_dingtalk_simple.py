#!/usr/bin/env python3
"""
简单的钉钉配置检查脚本
不依赖外部库
"""

import os
import json
import sys
from datetime import datetime

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def check_config():
    """检查钉钉配置"""
    print("🔍 钉钉配置检查")
    print("=" * 50)

    # 检查可能的配置文件
    config_locations = [
        os.path.join(PROJECT_ROOT, "config", "dingtalk.json"),
        os.path.join(PROJECT_ROOT, "dingtalk_config.json"),
        os.path.join(PROJECT_ROOT, ".dingtalk"),
        os.path.expanduser("~/.dingtalk_config"),
    ]

    found_configs = []

    for location in config_locations:
        if os.path.exists(location):
            try:
                with open(location, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 尝试解析JSON
                    try:
                        config = json.loads(content)
                        webhook = config.get('webhook', config.get('Webhook', ''))
                        if webhook:
                            found_configs.append({
                                'file': location,
                                'webhook': webhook[:50] + '...' if len(webhook) > 50 else webhook,
                                'full_webhook': webhook,
                                'config': config
                            })
                    except json.JSONDecodeError:
                        # 可能是其他格式
                        if 'dingtalk' in content.lower() or 'webhook' in content.lower():
                            found_configs.append({
                                'file': location,
                                'webhook': '非JSON格式',
                                'full_webhook': '',
                                'config': {'raw_content': content[:200]}
                            })
            except Exception as e:
                print(f"⚠️ 读取 {location} 失败: {e}")

    # 检查环境变量
    env_vars = ['DINGTALK_WEBHOOK', 'DINGTALK_TOKEN', 'DINGTALK_ACCESS_TOKEN']
    for env_var in env_vars:
        value = os.environ.get(env_var)
        if value:
            found_configs.append({
                'file': f'环境变量: {env_var}',
                'webhook': value[:50] + '...' if len(value) > 50 else value,
                'full_webhook': value,
                'config': {'source': 'environment'}
            })

    return found_configs

def generate_test_config():
    """生成测试配置文件"""
    print("\n📝 生成测试配置文件...")

    config_dir = os.path.join(PROJECT_ROOT, "config")
    os.makedirs(config_dir, exist_ok=True)

    # 创建示例配置文件
    example_config = {
        "name": "钉钉炒股助手配置",
        "description": "多Agent炒股系统钉钉集成配置",
        "webhook": "https://oapi.dingtalk.com/robot/send?access_token=YOUR_ACCESS_TOKEN_HERE",
        "secret": "YOUR_SECRET_HERE_IF_NEEDED",
        "at_mobiles": ["YOUR_MOBILE_HERE"],
        "settings": {
            "enable_alerts": True,
            "alert_types": ["买入信号", "卖出信号", "止损提醒", "热点推送"],
            "quiet_hours": ["22:00-08:00"],
            "rate_limit": 18
        },
        "user_profile": {
            "risk_level": "high",
            "holding_period": "1-3天",
            "preferred_sectors": ["AI", "新能源", "半导体"],
            "max_position_per_stock": 0.3,
            "daily_loss_limit": 0.05
        },
        "created_at": datetime.now().isoformat()
    }

    config_file = os.path.join(config_dir, "dingtalk_example.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(example_config, f, indent=2, ensure_ascii=False)

    print(f"✅ 示例配置文件已生成: {config_file}")

    # 创建配置说明
    readme_file = os.path.join(config_dir, "readme.md")
    readme_content = """# 钉钉集成配置说明

## 配置步骤

### 1. 创建钉钉机器人
1. 打开钉钉群 → 设置 → 智能群助手
2. 添加机器人 → 自定义
3. 设置机器人名称：`炒股助手Agent`
4. 安全设置（可选）：
   - 自定义关键词：`买入`、`卖出`、`预警`、`热点`
   - IP白名单：添加服务器IP
   - 签名校验：启用并记录Secret

### 2. 获取Webhook地址
格式：`https://oapi.dingtalk.com/robot/send?access_token=xxx`

### 3. 修改配置文件
编辑 `dingtalk.json`：
```json
{
  "webhook": "您的实际Webhook地址",
  "secret": "您的签名密钥（如有）",
  "at_mobiles": ["您的手机号"],
  "enable": true
}
```

### 4. 测试连接
运行测试脚本：
```bash
python test_dingtalk.py
```

## 消息类型

| 类型 | 关键词 | 说明 |
|------|--------|------|
| 买入信号 | 🚨 | 综合评分≥7.5，技术面+资金面共振 |
| 卖出信号 | 🔴 | 跌破止损或出现利空 |
| 止损提醒 | ⚠️ | 价格接近止损位 |
| 热点推送 | 🔔 | 板块涨幅>3%或资金大幅流入 |
| 午间复盘 | 📊 | 上午操作总结 |
| 收盘总结 | 📈 | 当日盈亏分析 |

## 安全建议
1. 不要公开Webhook地址
2. 启用钉钉安全设置
3. 定期更换访问令牌
4. 监控消息发送频率
"""

    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"✅ 配置说明已生成: {readme_file}")

    return config_file

def main():
    """主函数"""
    print("🤖 钉钉集成状态检查")
    print("=" * 50)

    # 检查现有配置
    configs = check_config()

    if configs:
        print(f"\n✅ 找到 {len(configs)} 个钉钉配置:")
        for i, config in enumerate(configs, 1):
            print(f"\n{i}. 来源: {config['file']}")
            print(f"   Webhook: {config['webhook']}")
            if 'config' in config and 'settings' in config['config']:
                print(f"   已启用: {config['config'].get('enable', True)}")

    else:
        print("\n❌ 未找到钉钉配置")

    print(f"\n{'='*50}")
    print("配置状态总结:")
    print(f"{'='*50}")

    if configs:
        print("🎯 状态: 已配置（需要验证连通性）")
        print("💡 下一步: 提供实际Webhook地址进行测试")
    else:
        print("🎯 状态: 未配置")
        print("💡 下一步: 创建钉钉机器人并获取Webhook")

    # 生成示例配置
    example_file = generate_test_config()

    print(f"\n{'='*50}")
    print("📋 操作指南:")
    print(f"{'='*50}")
    print("1. 按照 readme.md 创建钉钉机器人")
    print("2. 获取Webhook地址")
    print("3. 修改示例配置文件")
    print("4. 运行连通性测试")
    print(f"\n示例配置文件: {example_file}")

    # 创建快速测试脚本
    quick_test = """#!/bin/bash
echo "快速钉钉测试"
echo "请将您的钉钉Webhook地址填入以下命令:"
echo ""
echo "curl -H 'Content-Type: application/json' \\"
echo "  -d '{\"msgtype\":\"text\",\"text\":{\"content\":\"🤖 测试消息: 钉钉集成正常\"}}' \\"
echo "  YOUR_WEBHOOK_URL_HERE"
echo ""
echo "如果返回 {\"errcode\":0,\"errmsg\":\"ok\"} 表示成功"
"""

    test_script = os.path.join(PROJECT_ROOT, "quick_dingtalk_test.sh")
    with open(test_script, 'w', encoding='utf-8') as f:
        f.write(quick_test)

    os.chmod(test_script, 0o755)
    print(f"\n✅ 快速测试脚本: {test_script}")

if __name__ == "__main__":
    main()