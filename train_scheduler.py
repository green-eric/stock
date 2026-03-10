#!/usr/bin/env python3
"""
列车调度器 - 统一管理多Agent炒股系统的定期任务
支持进程监控、定时脚本执行和健康检查
"""

import json
import os
import sys
import subprocess
import threading
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

class TaskScheduler:
    def __init__(self, config_file="train_schedule_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.tasks = {}
        self.processes = {}
        self.running = False
        self.logger = self.setup_logging()

    def load_config(self):
        """加载配置文件"""
        config_path = Path(self.config_file)
        if not config_path.exists():
            default_config = {"tasks": [], "settings": {}}
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def setup_logging(self):
        """设置日志"""
        log_file = self.config.get('settings', {}).get('log_file', 'logs/train_scheduler.log')
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        logger = logging.getLogger('train_scheduler')
        logger.setLevel(logging.INFO)

        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 格式
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def run_command(self, task, task_type='oneshot'):
        """运行命令"""
        task_id = task['id']
        command = task['command']
        working_dir = task.get('working_dir', '.')
        description = task.get('description', '')

        self.logger.info(f"执行任务: {task['name']} ({description})")
        self.logger.debug(f"命令: {command}, 工作目录: {working_dir}")

        try:
            # 切换工作目录
            original_dir = os.getcwd()
            if working_dir != '.':
                os.chdir(working_dir)

            # 运行命令
            if task_type == 'process':
                # 长期运行进程
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8'
                )
                self.processes[task_id] = process
                self.logger.info(f"进程 {task_id} 启动, PID: {process.pid}")

                # 启动线程监控进程输出
                threading.Thread(
                    target=self.monitor_process_output,
                    args=(process, task_id),
                    daemon=True
                ).start()

            else:
                # 一次性脚本
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )

                if result.returncode == 0:
                    self.logger.info(f"任务 {task_id} 执行成功")
                    if result.stdout.strip():
                        self.logger.debug(f"输出: {result.stdout[:200]}...")
                else:
                    self.logger.error(f"任务 {task_id} 执行失败, 返回码: {result.returncode}")
                    if result.stderr.strip():
                        self.logger.error(f"错误: {result.stderr[:500]}...")

            # 恢复工作目录
            if working_dir != '.':
                os.chdir(original_dir)

        except Exception as e:
            self.logger.error(f"执行任务 {task_id} 时出错: {e}")
            if working_dir != '.':
                os.chdir(original_dir)

    def monitor_process_output(self, process, task_id):
        """监控进程输出"""
        try:
            stdout, stderr = process.communicate()
            if stdout:
                self.logger.info(f"进程 {task_id} 输出: {stdout[:500]}...")
            if stderr:
                self.logger.error(f"进程 {task_id} 错误: {stderr[:500]}...")

            returncode = process.returncode
            if returncode != 0:
                self.logger.warning(f"进程 {task_id} 退出, 返回码: {returncode}")
            else:
                self.logger.info(f"进程 {task_id} 正常退出")

        except Exception as e:
            self.logger.error(f"监控进程 {task_id} 时出错: {e}")

    def start_interval_tasks(self):
        """启动间隔任务"""
        for task in self.config['tasks']:
            if not task.get('enabled', True):
                continue

            task_type = task.get('type', 'script')
            if 'interval' in task:
                # 间隔任务
                interval = task['interval']
                task_id = task['id']

                self.logger.info(f"调度间隔任务: {task['name']}, 间隔: {interval}秒")

                # 启动任务线程
                thread = threading.Thread(
                    target=self.run_interval_task,
                    args=(task, interval),
                    daemon=True
                )
                thread.start()
                self.tasks[task_id] = thread

    def run_interval_task(self, task, interval):
        """运行间隔任务"""
        task_id = task['id']
        task_name = task['name']

        self.logger.info(f"开始间隔任务循环: {task_name}")

        while self.running:
            try:
                self.run_command(task, task_type='process' if task.get('type') == 'process' else 'oneshot')
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"间隔任务 {task_id} 出错: {e}")
                time.sleep(min(interval, 60))  # 出错后等待较短时间

    def start_scheduled_tasks(self):
        """启动定时任务"""
        # 这里可以使用schedule库，但为了简单，使用循环检查
        # 实际部署建议使用系统cron或schedule库
        self.logger.info("定时任务调度启动 (使用简单循环检查)")

        # 启动定时任务检查线程
        thread = threading.Thread(target=self.check_scheduled_tasks, daemon=True)
        thread.start()

    def check_scheduled_tasks(self):
        """检查定时任务"""
        while self.running:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_day = now.strftime("%a").lower()  # mon, tue, etc

            for task in self.config['tasks']:
                if not task.get('enabled', True):
                    continue

                if 'schedule' in task:
                    schedule_str = task['schedule']

                    # 简单解析schedule格式: "09:00" 或 "mon 09:00"
                    parts = schedule_str.split()
                    if len(parts) == 1:
                        # 仅时间
                        scheduled_time = parts[0]
                        day_match = True
                    elif len(parts) == 2:
                        # 星期 + 时间
                        scheduled_day, scheduled_time = parts
                        day_match = scheduled_day.lower() == current_day
                    else:
                        self.logger.warning(f"无法解析schedule格式: {schedule_str}")
                        continue

                    if day_match and scheduled_time == current_time:
                        self.logger.info(f"触发定时任务: {task['name']}")
                        # 在独立线程中运行任务
                        threading.Thread(
                            target=self.run_command,
                            args=(task, 'oneshot'),
                            daemon=True
                        ).start()

            # 每分钟检查一次
            time.sleep(60)

    def health_check(self):
        """健康检查"""
        self.logger.info("执行健康检查...")

        # 检查进程是否存活
        for task_id, process in list(self.processes.items()):
            if process.poll() is not None:
                self.logger.warning(f"进程 {task_id} 已停止, 返回码: {process.returncode}")
                # 可以在这里重启进程
                # 暂时只记录

        # 检查系统资源
        # 简化版本，可以扩展

        self.logger.info("健康检查完成")

    def start(self):
        """启动调度器"""
        self.logger.info("🚂 列车调度器启动")
        self.logger.info(f"加载配置: {self.config_file}")
        self.logger.info(f"任务数量: {len(self.config['tasks'])}")

        self.running = True

        # 启动间隔任务
        self.start_interval_tasks()

        # 启动定时任务
        self.start_scheduled_tasks()

        # 启动健康检查线程
        health_interval = self.config.get('settings', {}).get('health_check_interval', 300)
        threading.Thread(
            target=self.run_health_check,
            args=(health_interval,),
            daemon=True
        ).start()

        self.logger.info("✅ 调度器已启动，所有任务已调度")

        # 保持主线程运行
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("接收到中断信号，正在停止...")
            self.stop()

    def run_health_check(self, interval):
        """运行定期健康检查"""
        while self.running:
            time.sleep(interval)
            self.health_check()

    def stop(self):
        """停止调度器"""
        self.logger.info("正在停止调度器...")
        self.running = False

        # 停止所有进程
        for task_id, process in self.processes.items():
            self.logger.info(f"停止进程: {task_id}")
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                self.logger.error(f"停止进程 {task_id} 时出错: {e}")

        self.logger.info("调度器已停止")

    def status(self):
        """查看状态"""
        status_info = {
            "running": self.running,
            "tasks_count": len(self.tasks),
            "processes_count": len(self.processes),
            "tasks": []
        }

        for task in self.config['tasks']:
            task_status = {
                "id": task['id'],
                "name": task['name'],
                "enabled": task.get('enabled', True),
                "type": task.get('type', 'script'),
                "status": "unknown"
            }

            if task['id'] in self.processes:
                process = self.processes[task['id']]
                if process.poll() is None:
                    task_status['status'] = 'running'
                    task_status['pid'] = process.pid
                else:
                    task_status['status'] = 'stopped'
                    task_status['exit_code'] = process.returncode
            else:
                task_status['status'] = 'scheduled'

            status_info['tasks'].append(task_status)

        return status_info

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='列车调度器 - 统一管理定期任务')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'run-once'],
                       help='操作: start=启动调度器, stop=停止, status=状态, run-once=运行一次指定任务')
    parser.add_argument('--config', default='train_schedule_config.json',
                       help='配置文件路径')
    parser.add_argument('--task-id', help='任务ID (run-once操作时使用)')

    args = parser.parse_args()

    scheduler = TaskScheduler(args.config)

    if args.action == 'start':
        scheduler.start()
    elif args.action == 'stop':
        scheduler.stop()
    elif args.action == 'status':
        status = scheduler.status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    elif args.action == 'run-once':
        if not args.task_id:
            print("错误: run-once操作需要--task-id参数")
            return 1

        task = None
        for t in scheduler.config['tasks']:
            if t['id'] == args.task_id:
                task = t
                break

        if not task:
            print(f"错误: 未找到任务ID: {args.task_id}")
            return 1

        print(f"运行任务: {task['name']}")
        scheduler.run_command(task, 'oneshot')

if __name__ == '__main__':
    main()