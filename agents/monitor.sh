#!/bin/bash

# 简单监控脚本（兼容版）

echo "监控脚本启动 $(date)"
echo "这是一个简单的监控脚本，用于兼容性"

# 检查进程
ps aux | grep -E "python|agent" | grep -v grep

# 监控循环
while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 系统监控检查"
    sleep 60
done