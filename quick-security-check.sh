#!/bin/bash
# LobsterAI 快速安全检查脚本
# 用于快速验证关键安全设置

echo "🔍 LobsterAI 快速安全检查"
echo "=========================="
echo "检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. 检查技能目录权限
echo "1. 技能目录权限检查"
echo "------------------"
skills_dir="/workspace/project/SKILLs"
if [[ -d "$skills_dir" ]]; then
    perms=$(stat -c "%a" "$skills_dir")
    owner=$(stat -c "%U:%G" "$skills_dir")

    if [[ "$perms" == "755" || "$perms" == "750" ]]; then
        echo "   ✅ 目录权限: $perms (正常)"
    else
        echo "   ⚠️  目录权限: $perms (建议改为755或750)"
    fi

    if [[ "$owner" == "root:root" ]]; then
        echo "   ✅ 目录所有者: $owner (正常)"
    else
        echo "   ⚠️  目录所有者: $owner (建议为root:root)"
    fi

    # 检查文件数量
    skill_count=$(ls -1 "$skills_dir" | wc -l)
    echo "   📊 技能数量: $skill_count"
else
    echo "   ❌ 技能目录不存在: $skills_dir"
fi
echo ""

# 2. 检查网络服务
echo "2. 网络服务检查"
echo "--------------"
# 检查web-search服务
if ps aux | grep -q "web-search.*server"; then
    echo "   ✅ web-search服务器: 运行中"

    # 检查端口
    if netstat -tunlp 2>/dev/null | grep -q ":8923"; then
        echo "   ✅ 端口8923: 监听中"
    else
        echo "   ⚠️  端口8923: 未监听"
    fi
else
    echo "   ℹ️  web-search服务器: 未运行"
fi

# 检查外部连接
ext_conn=$(netstat -tunap 2>/dev/null | grep -E "(ESTABLISHED)" | grep -v "127.0.0.1" | wc -l)
echo "   📡 外部连接数: $ext_conn"
echo ""

# 3. 检查进程安全
echo "3. 进程安全检查"
echo "--------------"
# 检查技能相关进程
skill_procs=$(ps aux | grep -E "(web-search|scheduled-task|imap-smtp)" | grep -v grep | wc -l)
echo "   🔄 技能相关进程: $skill_procs"

# 检查root进程
root_procs=$(ps aux | grep "^root" | wc -l)
echo "   👑 root进程数: $root_procs"
echo ""

# 4. 检查文件系统
echo "4. 文件系统检查"
echo "--------------"
# 检查磁盘使用
disk_usage=$(df -h /workspace | tail -1 | awk '{print $5}')
echo "   💾 磁盘使用率: $disk_usage"

# 检查最近修改
recent_files=$(find "$skills_dir" -type f -mtime -1 2>/dev/null | wc -l)
echo "   📝 最近24小时修改文件: $recent_files"
echo ""

# 5. 检查定时任务
echo "5. 定时任务检查"
echo "--------------"
if command -v crontab > /dev/null 2>&1; then
    cron_count=$(crontab -l 2>/dev/null | grep -c -v "^#" | tr -d ' ')
    echo "   ⏰ Cron任务数: $cron_count"

    if [[ $cron_count -gt 0 ]]; then
        echo "   最近任务:"
        crontab -l 2>/dev/null | grep -v "^#" | head -2 | while read task; do
            echo "     • $task"
        done
    fi
else
    echo "   ℹ️  crontab不可用"
fi
echo ""

# 6. 安全检查总结
echo "6. 安全检查总结"
echo "--------------"
echo "   📊 总体安全状态:"

# 计算安全分数
security_score=100

# 权限检查扣分
if [[ "$perms" != "755" && "$perms" != "750" ]]; then
    security_score=$((security_score - 10))
fi

# 网络连接扣分
if [[ $ext_conn -gt 5 ]]; then
    security_score=$((security_score - 5))
fi

# 最近修改文件扣分
if [[ $recent_files -gt 100 ]]; then
    security_score=$((security_score - 5))
fi

# 显示安全等级
if [[ $security_score -ge 90 ]]; then
    echo "   ✅ 安全等级: 优秀 ($security_score/100)"
elif [[ $security_score -ge 70 ]]; then
    echo "   ⚠️  安全等级: 良好 ($security_score/100)"
elif [[ $security_score -ge 50 ]]; then
    echo "   ⚠️  安全等级: 中等 ($security_score/100)"
else
    echo "   ❌ 安全等级: 差 ($security_score/100)"
fi

echo ""
echo "📋 建议操作:"
echo "   1. 定期运行完整安全监控: ./skill-security-monitor.sh"
echo "   2. 查看详细安全报告: ls -la /workspace/project/security-report-*.txt"
echo "   3. 阅读安全建议: cat /workspace/project/security-recommendations.md"
echo ""
echo "🔧 快速修复命令:"
echo "   # 修复目录权限"
echo "   sudo chmod 750 /workspace/project/SKILLs"
echo "   sudo chown -R root:root /workspace/project/SKILLs"
echo ""
echo "检查完成! 🎯"