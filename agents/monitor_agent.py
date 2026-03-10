#!/usr/bin/env python3
"""
系统监控Agent
监控各Agent状态和系统健康
"""

import time
import psutil
import json
from datetime import datetime
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
from dingtalk_sender import DingTalkSender

class MonitorAgent:
    def __init__(self):
        self.sender = DingTalkSender()
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(project_root, "logs")
        self.agents = {
            "data_agent": {"pid_file": os.path.join(logs_dir, "data_agent.pid"), "name": "数据采集"},
            "technical_agent": {"pid_file": os.path.join(logs_dir, "technical_agent.pid"), "name": "技术分析"}
        }

    def check_agent_status(self):
        """检查Agent状态"""
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

                    if psutil.pid_exists(pid):
                        status[agent_id]["running"] = True
                        status[agent_id]["pid"] = pid

                        # 获取进程资源使用
                        try:
                            process = psutil.Process(pid)
                            status[agent_id]["cpu_percent"] = process.cpu_percent()
                            status[agent_id]["memory_mb"] = process.memory_info().rss / 1024 / 1024
                        except:
                            pass
                except:
                    pass

        return status

    def check_system_resources(self):
        """检查系统资源"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        # 跨平台磁盘使用率检查
        if os.name == 'nt':  # Windows
            disk_root = 'C:\\'
        else:
            disk_root = '/'
        disk = psutil.disk_usage(disk_root)

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / 1024 / 1024 / 1024,
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / 1024 / 1024 / 1024
        }

    def send_status_report(self):
        """发送状态报告到钉钉"""
        agent_status = self.check_agent_status()
        system_resources = self.check_system_resources()

        # 构造消息内容
        content = f"""
🤖 系统状态报告
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

                if "cpu_percent" in status:
                    content += f" [CPU: {status['cpu_percent']:.1f}%]"
                if "memory_mb" in status:
                    content += f" [内存: {status['memory_mb']:.1f}MB]"
            else:
                content += "未运行"

            content += "\n"

        content += f"""
📊 系统资源:
- CPU使用率: {system_resources['cpu_percent']:.1f}%
- 内存使用: {system_resources['memory_percent']:.1f}% ({system_resources['memory_used_gb']:.2f}GB)
- 磁盘使用: {system_resources['disk_percent']:.1f}% (剩余: {system_resources['disk_free_gb']:.2f}GB)

📈 运行统计:
- 运行Agent: {running_count}/{len(agent_status)}
- 系统状态: {'正常' if running_count == len(agent_status) else '异常'}

💡 提示: 所有Agent正常运行表示系统健康
"""

        # 如果有Agent异常，提高消息级别
        level = "warning" if running_count < len(agent_status) else "info"

        self.sender.send_message(
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
                "system_resources": system_resources
            }, f, indent=2, ensure_ascii=False)

        return running_count

    def run(self, interval=1800):  # 默认30分钟
        """运行监控Agent"""
        print(f"监控Agent启动，间隔: {interval}秒")

        # 首次启动发送通知
        self.send_startup_notification()

        while True:
            try:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 检查系统状态...")
                running_count = self.send_status_report()

                if running_count < len(self.agents):
                    print(f"警告: 只有 {running_count}/{len(self.agents)} 个Agent在运行")

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n监控Agent停止")
                break
            except Exception as e:
                print(f"监控错误: {e}")
                time.sleep(60)

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
- 买入/卖出信号实时推送
- 市场热点定时更新
- 系统状态监控告警

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

if __name__ == "__main__":
    agent = MonitorAgent()
    agent.run(interval=1800)  # 30分钟间隔
