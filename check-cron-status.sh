#!/bin/bash
# cron服务状态检查脚本

echo "=== Cron服务状态检查 ==="
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 检查cron服务是否运行
echo "## 1. Cron服务状态"
if ps aux | grep -q "[c]rond"; then
    echo "  ✅ cron服务: 运行中"
    CRON_PID=$(ps aux | grep "[c]rond" | awk '{print $2}')
    echo "  PID: $CRON_PID"
else
    echo "  ❌ cron服务: 未运行"
    echo "  启动命令: crond"
fi
echo ""

# 检查cron配置
echo "## 2. Cron配置"
echo "当前用户: $(whoami)"
echo "crontab条目数: $(crontab -l 2>/dev/null | grep -v "^#" | wc -l)"
echo ""
echo "已配置的任务:"
crontab -l 2>/dev/null | grep -v "^#" | while read line; do
    if [ -n "$line" ]; then
        echo "  📋 $line"
    fi
done
echo ""

# 检查技能检查任务
echo "## 3. 技能检查任务状态"
SKILL_CHECK=$(crontab -l 2>/dev/null | grep "check-skill-updates.sh")
if [ -n "$SKILL_CHECK" ]; then
    echo "  ✅ 技能检查任务: 已配置"
    echo "  执行时间: $(echo "$SKILL_CHECK" | awk '{print $2":"$1" 每日"}') (UTC)"
    echo "  对应北京时间: 17:00 (UTC+8)"
    echo "  命令: $(echo "$SKILL_CHECK" | cut -d' ' -f7-)"
else
    echo "  ❌ 技能检查任务: 未配置"
fi
echo ""

# 检查日志文件
echo "## 4. 日志文件状态"
LOG_FILE="/workspace/project/skill-updates.log"
if [ -f "$LOG_FILE" ]; then
    echo "  ✅ 日志文件: 存在"
    echo "  文件大小: $(ls -lh "$LOG_FILE" | awk '{print $5}')"
    echo "  最后修改: $(stat -c %y "$LOG_FILE" | cut -d'.' -f1)"
    echo "  最近记录:"
    tail -3 "$LOG_FILE" | grep -E "^检查时间:|^已安装技能数量:" | while read line; do
        echo "    📝 $line"
    done
else
    echo "  📝 日志文件: 尚未创建 (将在第一次运行时创建)"
fi
echo ""

# 检查脚本可执行性
echo "## 5. 脚本状态"
SCRIPT="/workspace/project/check-skill-updates.sh"
if [ -x "$SCRIPT" ]; then
    echo "  ✅ 检查脚本: 可执行"
    echo "  脚本路径: $SCRIPT"
    echo "  脚本大小: $(wc -l < "$SCRIPT") 行"
else
    echo "  ❌ 检查脚本: 不可执行或不存在"
    echo "  修复命令: chmod +x $SCRIPT"
fi
echo ""

echo "=== 检查完成 ==="
echo ""
echo "## 手动测试命令:"
echo "1. 运行技能检查: bash /workspace/project/check-skill-updates.sh"
echo "2. 查看cron日志: tail -f /var/log/cron (如果可用)"
echo "3. 查看技能日志: tail -f /workspace/project/skill-updates.log"
echo ""
echo "## 问题排查:"
echo "如果cron任务未执行，请检查:"
echo "1. cron服务是否运行: ps aux | grep crond"
echo "2. 系统时间是否正确: date"
echo "3. 脚本权限: ls -la /workspace/project/check-skill-updates.sh"
echo "4. 手动测试脚本: bash /workspace/project/check-skill-updates.sh"