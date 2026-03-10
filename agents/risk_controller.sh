#!/bin/bash
AGENT_ID="$1"
AGENT_NAME="$2"
LOG_FILE="$3"

echo "$(date '+%Y-%m-%d %H:%M:%S') - $AGENT_NAME 启动成功" >> "$LOG_FILE"

# 模拟Agent工作循环
while true; do
    sleep 5
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $AGENT_NAME 正常运行" >> "$LOG_FILE"
done
