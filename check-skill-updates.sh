#!/bin/bash
# 技能更新检查脚本
# 每日自动检查技能状态和版本

echo "=== LobsterAI 技能更新检查 ==="
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "系统时间: $(date)"
echo ""

# 1. 检查技能目录结构
echo "## 技能目录结构"
SKILLS_COUNT=$(ls -d /workspace/project/SKILLs/*/ 2>/dev/null | wc -l)
echo "已安装技能数量: $SKILLS_COUNT"
echo "技能目录: /workspace/project/SKILLs/"
ls -d /workspace/project/SKILLs/*/ 2>/dev/null | xargs -I {} basename {} | sort | tr '\n' ' '
echo ""
echo ""

# 2. 检查关键技能状态
echo "## 关键技能状态检查"

# token-optimizer 检查
echo "### 1. token-optimizer (成本优化)"
if [ -f "/workspace/project/SKILLs/lobsterai-skill-zip-cJLsX1/CHANGELOG.md" ]; then
    VERSION=$(grep -E "\[[0-9]+\.[0-9]+\.[0-9]+\]" /workspace/project/SKILLs/lobsterai-skill-zip-cJLsX1/CHANGELOG.md | head -1 | sed 's/.*\[//;s/\].*//')
    echo "  版本: $VERSION"
    echo "  路径: /workspace/project/SKILLs/lobsterai-skill-zip-cJLsX1/"

    # 检查健康状态
    if [ -f "/workspace/project/SKILLs/lobsterai-skill-zip-cJLsX1/cli.py" ]; then
        cd /workspace/project/SKILLs/lobsterai-skill-zip-cJLsX1
        echo "  健康检查:"
        python cli.py health 2>&1 | grep -E "\[(PASS|FAIL|SKIP)\]" | while read line; do
            echo "    $line"
        done
    fi
else
    echo "  状态: 未安装或文件缺失"
fi
echo ""

# web-search 检查 (股票查询相关)
echo "### 2. web-search (网络搜索)"
if [ -d "/workspace/project/SKILLs/web-search" ]; then
    echo "  状态: 已安装"
    # 检查服务器状态
    if ps aux | grep -q "web-search.*server"; then
        echo "  服务器: 运行中"
    else
        echo "  服务器: 未运行 (需要时手动启动)"
    fi
else
    echo "  状态: 未安装"
fi
echo ""

# scheduled-task 检查
echo "### 3. scheduled-task (定时任务)"
if [ -d "/workspace/project/SKILLs/scheduled-task" ]; then
    echo "  状态: 已安装"
    if [ -f "/workspace/project/SKILLs/scheduled-task/scripts/create-task.sh" ]; then
        echo "  脚本: 可用"
    fi
else
    echo "  状态: 未安装"
fi
echo ""

# 3. 检查与股票查询相关的技能
echo "## 股票查询相关技能"
echo "### 1. data-analysis (数据分析)"
[ -d "/workspace/project/SKILLs/data-analysis" ] && echo "  状态: 已安装" || echo "  状态: 未安装"

echo "### 2. chart-visualization (图表可视化)"
[ -d "/workspace/project/SKILLs/chart-visualization" ] && echo "  状态: 已安装" || echo "  状态: 未安装"

echo "### 3. technology-news-search (科技新闻搜索)"
[ -d "/workspace/project/SKILLs/technology-news-search" ] && echo "  状态: 已安装" || echo "  状态: 未安装"
echo ""

# 4. 系统资源检查
echo "## 系统资源状态"
echo "内存使用:"
free -h | grep -E "^Mem:" | awk '{print "  总量: "$2, "已用: "$3, "可用: "$4, "使用率: "$3"/"$2}'
echo ""
echo "磁盘空间:"
df -h / | grep -v Filesystem | awk '{print "  总量: "$2, "已用: "$3, "可用: "$4, "使用率: "$5}'
echo ""
echo "CPU信息:"
lscpu | grep -E "Model name|CPU\(s\)" | head -2 | while read line; do
    echo "  $line"
done
echo ""

# 5. 检查是否有更新日志
echo "## 技能更新日志"
LOG_FILE="/workspace/project/skill-updates.log"
if [ -f "$LOG_FILE" ]; then
    echo "最近检查记录:"
    tail -5 "$LOG_FILE" | grep -E "^检查时间:|^已安装技能数量:" | while read line; do
        echo "  $line"
    done
    echo "完整日志: $LOG_FILE"
else
    echo "  暂无检查记录"
fi
echo ""

echo "=== 检查完成 ==="
echo "下次检查: 每日 09:00 (Asia/Shanghai)"
echo "日志文件: /workspace/project/skill-updates.log"
echo "手动运行: bash /workspace/project/check-skill-updates.sh"