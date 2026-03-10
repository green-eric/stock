#!/usr/bin/env python3
"""
简化版系统监控Agent
不依赖psutil，基础监控功能
"""

import time
import json
import os
import subprocess
from datetime import datetime
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dingtalk_sender import DingTalkSender

class SimpleMonitorAgent:
    def __init__(self):
        self.sender = DingTalkSender()
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.agents = {
            "data_agent": {"pid_file": os.path.join(project_root, "agents", "data_agent.pid"), "name": "数据采集"},
            "technical_agent": {"pid_file": os.path.join(project_root, "agents", "technical_agent.pid"), "name": "技术分析"}
        }

    def check_agent_status_simple(self):
        """简化版Agent状态检查"""
        status = {}

        for agent_id, info in self.agents.items():
            pid_file = info["pid_file"]
            status[agent_id] = {
                "name": info["name"],
                "running": False,
                "pid": None
            }

            if os.path.exists(pid_file):
                try:
                    with open(pid_file, 'r') as f:
                        pid = int(f.read().strip())

                    # 简单检查进程是否存在
                    try:
                        os.kill(pid, 0)  # 发送0信号检查进程
                        status[agent_id]["running"] = True
                        status[agent_id]["pid"] = pid
                    except OSError:
                        status[agent_id]["running"] = False
                except:
                    status[agent_id]["running"] = False

        return status

    def check_system_resources_simple(self):
        """简化版系统资源检查"""
        # 使用系统命令检查资源
        try:
            # 检查内存使用
            mem_result = subprocess.run(
                ["free", "-m"],
                capture_output=True,
                text=True
            )

            # 检查磁盘使用
            disk_result = subprocess.run(
                ["df", "-h", "/"],
                capture_output=True,
                text=True
            )

            return {
                "memory_info": mem_result.stdout[:200] if mem_result.stdout else "N/A",
                "disk_info": disk_result.stdout[:200] if disk_result.stdout else "N/A",
                "timestamp": datetime.now().isoformat()
            }
        except:
            return {
                "memory_info": "检查失败",
                "disk_info": "检查失败",
                "timestamp": datetime.now().isoformat()
            }

    def send_status_report(self):
        """发送状态报告到钉钉"""
        agent_status = self.check_agent_status_simple()
        system_resources = self.check_system_resources_simple()

        # 构造消息内容
        content = f"""
🤖 系统状态报告 (简化版)
⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔧 Agent状态:
"""

        running_count = 0
        for agent_id, status in agent_status.items():
            status_icon = "✅" if status["running"] else "❌"
            content += f"- {status_icon} {status['name']}: "

            if status["running"]:
                running_count += 1
                content += f"运行中 (PID: {status['pid']})"
            else:
                content += "未运行"

            content += "\n"

        content += f"""
📊 运行统计:
- 运行Agent: {running_count}/{len(agent_status)}
- 系统状态: {'正常' if running_count == len(agent_status) else '异常'}

💡 提示: 所有Agent正常运行表示系统健康
"""

        # 如果有Agent异常，提高消息级别
        level = "warning" if running_count < len(agent_status) else "info"

        success = self.sender.send_message(
            title="🤖 系统状态报告",
            content=content,
            msg_type="markdown",
            level=level
        )

        # 保存状态
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)

        status_file = os.path.join(data_dir, f"system_status_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "agent_status": agent_status,
                "system_resources": system_resources,
                "running_count": running_count
            }, f, indent=2, ensure_ascii=False)

        return success

    def send_startup_notification(self):
        """发送启动通知"""
        content = f"""
🎉 多Agent炒股系统启动成功!

🤖 系统信息:
- 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 用户模式: 散户超短线 (1-3天)
- 运行环境: 沙箱VM

🚀 已启动Agent:
1. 数据采集Agent - 每5分钟更新市场数据
2. 技术分析Agent - 每15分钟分析股票
3. 监控Agent - 每30分钟报告状态

📱 钉钉集成:
- ✅ 签名校验: 已启用
- ✅ 关键词匹配: 已配置
- ✅ 实时推送: 买入/卖出/止损信号

💡 使用提示:
发送'帮助'到钉钉机器人查看可用指令

⏰ 系统状态: 运行中
"""

        self.sender.send_message(
            title="🎉 多Agent炒股系统启动",
            content=content,
            msg_type="markdown",
            level="info"
        )

    def run(self, interval=1800):  # 默认30分钟
        """运行监控Agent"""
        print(f"简化版监控Agent启动，间隔: {interval}秒")

        # 首次启动发送通知
        self.send_startup_notification()

        while True:
            try:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 检查系统状态...")
                success = self.send_status_report()

                if success:
                    print(f"状态报告发送成功")
                else:
                    print(f"状态报告发送失败")

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n监控Agent停止")
                break
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(60)

if __name__ == "__main__":
    agent = SimpleMonitorAgent()
    agent.run(interval=1800)  # 30分钟间隔