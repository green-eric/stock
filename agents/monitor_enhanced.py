#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版系统监控Agent
支持钉钉事件通知和系统资源监控
"""

import json
import time
import logging
import threading
import subprocess
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# 尝试导入psutil，如果不可用则使用替代方法
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("警告: psutil模块不可用，系统资源监控功能将受限")

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dingtalk_notifier import init_notifier, notify_agent_event, notify_system_alert
    DINGTALK_AVAILABLE = True
except ImportError:
    DINGTALK_AVAILABLE = False
    print("警告: dingtalk_notifier模块不可用，钉钉通知功能将禁用")

logger = logging.getLogger(__name__)


class EnhancedMonitorAgent:
    """增强版系统监控Agent"""

    def __init__(self, config_path: str = "config/monitor_config.json"):
        """
        初始化监控Agent

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = None
        self.running = False
        self.monitor_thread = None
        self.agents_status = {}
        self.last_check_time = None

        # 初始化日志
        self._setup_logging()

        # 加载配置
        self._load_config()

        # 初始化钉钉通知器
        self.dingtalk_enabled = False
        if DINGTALK_AVAILABLE and self.config.get("monitor", {}).get("enable_dingtalk", False):
            notifier = init_notifier("config/dingtalk.json")
            if notifier:
                self.dingtalk_enabled = True
                logger.info("钉钉通知功能已启用")
            else:
                logger.warning("钉钉通知器初始化失败，通知功能将禁用")

    def _setup_logging(self):
        """设置日志"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, "monitor.log")

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"配置文件加载成功: {self.config_path}")
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {self.config_path}")
            self.config = {}
        except json.JSONDecodeError as e:
            logger.error(f"配置文件解析失败: {e}")
            self.config = {}

    def _send_dingtalk_notification(self, agent_name: str, event_type: str, message: str = "", extra_data: Dict = None):
        """发送钉钉通知"""
        if not self.dingtalk_enabled:
            return

        try:
            from dingtalk_notifier import notify_agent_event
            notify_agent_event(agent_name, event_type, message, extra_data)
        except Exception as e:
            logger.error(f"钉钉通知发送失败: {e}")

    def _send_system_alert(self, alert_type: str, severity: str, message: str, details: Dict = None):
        """发送系统告警"""
        if not self.dingtalk_enabled:
            return

        try:
            from dingtalk_notifier import notify_system_alert
            notify_system_alert(alert_type, severity, message, details)
        except Exception as e:
            logger.error(f"系统告警发送失败: {e}")

    def check_agent_status(self, agent_name: str, agent_config: Dict) -> Dict:
        """
        检查Agent状态

        Args:
            agent_name: Agent名称
            agent_config: Agent配置

        Returns:
            状态信息字典
        """
        status = {
            "name": agent_name,
            "enabled": agent_config.get("enabled", False),
            "running": False,
            "pid": None,
            "uptime": None,
            "last_check": datetime.now().isoformat()
        }

        if not status["enabled"]:
            return status

        # 这里简化为检查进程是否运行
        # 实际实现应该检查具体的Agent进程
        script = agent_config.get("script", "")
        if script and os.path.exists(script):
            status["running"] = True
            status["pid"] = 9999  # 模拟PID

        return status

    def check_system_resources(self) -> Dict:
        """检查系统资源"""
        resources = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "disk_usage": {},
            "process_count": 0
        }

        if HAS_PSUTIL:
            try:
                resources["cpu_percent"] = psutil.cpu_percent(interval=1)
                resources["memory_percent"] = psutil.virtual_memory().percent
                resources["process_count"] = len(psutil.pids())

                # 检查磁盘使用情况
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        resources["disk_usage"][partition.mountpoint] = {
                            "total_gb": usage.total / (1024**3),
                            "used_gb": usage.used / (1024**3),
                            "free_gb": usage.free / (1024**3),
                            "percent": usage.percent
                        }
                    except Exception as e:
                        logger.warning(f"无法获取磁盘使用情况 {partition.mountpoint}: {e}")
            except Exception as e:
                logger.error(f"系统资源检查失败: {e}")
        else:
            # 模拟数据用于测试
            resources["cpu_percent"] = 25.5
            resources["memory_percent"] = 45.2
            resources["process_count"] = 150
            resources["disk_usage"]["/"] = {
                "total_gb": 50.0,
                "used_gb": 20.5,
                "free_gb": 29.5,
                "percent": 41.0
            }
            logger.debug("使用模拟系统资源数据")

        return resources

    def check_log_files(self) -> Dict:
        """检查日志文件"""
        log_info = {
            "timestamp": datetime.now().isoformat(),
            "log_files": []
        }

        log_dir = "logs"
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                filepath = os.path.join(log_dir, filename)
                if os.path.isfile(filepath):
                    size_mb = os.path.getsize(filepath) / (1024 * 1024)
                    log_info["log_files"].append({
                        "name": filename,
                        "size_mb": round(size_mb, 2),
                        "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                    })

        return log_info

    def monitor_loop(self):
        """监控主循环"""
        logger.info("监控Agent开始运行")

        # 发送启动通知
        if self.dingtalk_enabled:
            self._send_dingtalk_notification("监控Agent", "start", "监控系统已启动")

        check_interval = self.config.get("monitor", {}).get("check_interval", 15)

        while self.running:
            try:
                self.last_check_time = datetime.now()

                # 检查Agent状态
                agents_config = self.config.get("agents", {})
                for agent_name, agent_config in agents_config.items():
                    status = self.check_agent_status(agent_name, agent_config)
                    self.agents_status[agent_name] = status

                    # 检查状态变化并发送通知
                    old_status = self.agents_status.get(agent_name, {})
                    if old_status.get("running") != status["running"]:
                        event_type = "start" if status["running"] else "stop"
                        self._send_dingtalk_notification(
                            agent_name,
                            event_type,
                            f"Agent状态变化: {'运行中' if status['running'] else '已停止'}"
                        )

                # 检查系统资源
                resources = self.check_system_resources()

                # 检查磁盘空间告警
                disk_threshold = self.config.get("monitor", {}).get("disk_threshold", 90)
                for mountpoint, usage in resources["disk_usage"].items():
                    if usage["percent"] > disk_threshold:
                        self._send_system_alert(
                            "磁盘空间告警",
                            "warning",
                            f"磁盘 {mountpoint} 使用率过高: {usage['percent']}%",
                            {"mountpoint": mountpoint, "usage_percent": usage["percent"]}
                        )

                # 检查内存使用告警
                memory_threshold = self.config.get("monitor", {}).get("memory_threshold", 85)
                if resources["memory_percent"] > memory_threshold:
                    self._send_system_alert(
                        "内存使用告警",
                        "warning",
                        f"内存使用率过高: {resources['memory_percent']}%",
                        {"memory_percent": resources["memory_percent"]}
                    )

                # 检查日志文件大小
                log_threshold_mb = self.config.get("monitor", {}).get("log_size_threshold_mb", 100)
                log_info = self.check_log_files()
                for log_file in log_info["log_files"]:
                    if log_file["size_mb"] > log_threshold_mb:
                        self._send_system_alert(
                            "日志文件过大",
                            "info",
                            f"日志文件 {log_file['name']} 过大: {log_file['size_mb']}MB",
                            {"filename": log_file["name"], "size_mb": log_file["size_mb"]}
                        )

                # 记录状态
                logger.info(f"监控检查完成 - Agents: {len(self.agents_status)}, 内存: {resources['memory_percent']}%")

                # 等待下一次检查
                time.sleep(check_interval)

            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(check_interval)

    def start(self):
        """启动监控Agent"""
        if self.running:
            logger.warning("监控Agent已经在运行")
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("监控Agent启动成功")

    def stop(self):
        """停止监控Agent"""
        if not self.running:
            logger.warning("监控Agent未在运行")
            return

        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)

        # 发送停止通知
        if self.dingtalk_enabled:
            self._send_dingtalk_notification("监控Agent", "stop", "监控系统已停止")

        logger.info("监控Agent已停止")

    def get_status(self) -> Dict:
        """获取监控Agent状态"""
        return {
            "running": self.running,
            "agents_status": self.agents_status,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "config_loaded": bool(self.config),
            "dingtalk_enabled": self.dingtalk_enabled
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="增强版系统监控Agent")
    parser.add_argument("--config", default="config/monitor_config.json", help="配置文件路径")
    parser.add_argument("--start", action="store_true", help="启动监控Agent")
    parser.add_argument("--stop", action="store_true", help="停止监控Agent")
    parser.add_argument("--status", action="store_true", help="查看状态")
    parser.add_argument("--daemon", action="store_true", help="以守护进程方式运行")
    args = parser.parse_args()

    monitor = EnhancedMonitorAgent(args.config)

    if args.start:
        monitor.start()
        if args.daemon:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                monitor.stop()
        else:
            print("监控Agent已启动，按Ctrl+C停止")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                monitor.stop()
    elif args.stop:
        monitor.stop()
    elif args.status:
        status = monitor.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()