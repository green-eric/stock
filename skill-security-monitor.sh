#!/bin/bash
# LobsterAI 技能安全监控系统
# 版本: 1.0.0
# 创建时间: 2026-03-08

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志文件
LOG_FILE="/workspace/project/security-monitor.log"
SKILLS_DIR="/workspace/project/SKILLs"

# 危险模式列表
DANGEROUS_PATTERNS=(
    "rm.*-rf"
    "chmod.*777"
    "wget.*http.*\\|.*sh"
    "curl.*http.*\\|.*sh"
    "bash.*<.*\\("
    "python.*-c.*exec"
    "eval.*\\$"
    "system\\(.*\\)"
    "exec\\(.*\\)"
    "popen\\(.*\\)"
    "subprocess\\.Popen"
    "os\\.system"
)

log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case "$level" in
        "INFO") echo -e "${BLUE}[INFO]${NC} $message" ;;
        "WARN") echo -e "${YELLOW}[WARN]${NC} $message" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
    esac

    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

check_permissions() {
    log_message "INFO" "检查技能目录权限..."

    # 检查目录权限
    local dir_perms=$(stat -c "%a" "$SKILLS_DIR")
    if [[ "$dir_perms" != "755" && "$dir_perms" != "750" ]]; then
        log_message "WARN" "技能目录权限异常: $dir_perms (应为 755 或 750)"
    else
        log_message "SUCCESS" "技能目录权限正常: $dir_perms"
    fi

    # 检查文件所有者
    local owner=$(stat -c "%U:%G" "$SKILLS_DIR")
    if [[ "$owner" != "root:root" ]]; then
        log_message "WARN" "技能目录所有者异常: $owner (应为 root:root)"
    else
        log_message "SUCCESS" "技能目录所有者正常: $owner"
    fi

    # 检查setuid/setgid文件
    log_message "INFO" "检查setuid/setgid文件..."
    local setuid_files=$(find "$SKILLS_DIR" -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | wc -l)
    if [[ $setuid_files -gt 0 ]]; then
        log_message "ERROR" "发现 $setuid_files 个setuid/setgid文件!"
        find "$SKILLS_DIR" -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | while read file; do
            log_message "ERROR" "  ⚠️ $file"
        done
    else
        log_message "SUCCESS" "未发现setuid/setgid文件"
    fi
}

check_script_safety() {
    log_message "INFO" "检查脚本安全性..."

    local dangerous_count=0

    for pattern in "${DANGEROUS_PATTERNS[@]}"; do
        log_message "INFO" "检查模式: $pattern"
        find "$SKILLS_DIR" -type f \( -name "*.sh" -o -name "*.py" -o -name "*.js" \) -exec grep -l "$pattern" {} \; 2>/dev/null | while read file; do
            log_message "WARN" "  发现危险模式: $file"
            dangerous_count=$((dangerous_count + 1))
        done
    done

    if [[ $dangerous_count -eq 0 ]]; then
        log_message "SUCCESS" "未发现危险脚本模式"
    else
        log_message "ERROR" "发现 $dangerous_count 个危险脚本模式"
    fi
}

check_network_access() {
    log_message "INFO" "检查网络访问..."

    # 检查web-search服务器
    if ps aux | grep -q "web-search.*server"; then
        log_message "INFO" "web-search服务器: 运行中"

        # 检查端口监听
        if netstat -tunlp 2>/dev/null | grep -q ":8923"; then
            log_message "INFO" "  端口8923: 监听中"
        fi
    else
        log_message "INFO" "web-search服务器: 未运行"
    fi

    # 检查其他网络连接
    log_message "INFO" "当前网络连接状态:"
    netstat -tunap 2>/dev/null | grep -E "(ESTABLISHED|LISTEN)" | grep -v "127.0.0.1" | head -5 | while read line; do
        log_message "INFO" "  $line"
    done
}

check_file_operations() {
    log_message "INFO" "检查文件操作监控..."

    # 检查最近修改的文件
    local recent_files=$(find "$SKILLS_DIR" -type f -mtime -1 2>/dev/null | wc -l)
    if [[ $recent_files -gt 0 ]]; then
        log_message "INFO" "发现 $recent_files 个最近修改的文件:"
        find "$SKILLS_DIR" -type f -mtime -1 2>/dev/null | head -5 | while read file; do
            local skill_name=$(basename "$(dirname "$file")")
            local filename=$(basename "$file")
            log_message "INFO" "  $skill_name/$filename"
        done
    else
        log_message "INFO" "最近24小时内无文件修改"
    fi

    # 检查关键目录
    local critical_dirs=("/root" "/etc" "/var" "/usr")
    for dir in "${critical_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            local modified_count=$(find "$dir" -type f -mtime -1 2>/dev/null | wc -l)
            if [[ $modified_count -gt 0 ]]; then
                log_message "WARN" "关键目录 $dir 有 $modified_count 个最近修改的文件"
            fi
        fi
    done
}

check_scheduled_tasks() {
    log_message "INFO" "检查定时任务..."

    # 检查cron任务
    if command -v crontab > /dev/null 2>&1; then
        local cron_count=$(crontab -l 2>/dev/null | grep -c -v "^#" | tr -d ' ')
        if [[ $cron_count -gt 0 ]]; then
            log_message "INFO" "发现 $cron_count 个cron任务"
            crontab -l 2>/dev/null | grep -v "^#" | head -3 | while read task; do
                log_message "INFO" "  $task"
            done
        else
            log_message "INFO" "未发现cron任务"
        fi
    fi

    # 检查systemd定时器
    if command -v systemctl > /dev/null 2>&1; then
        local timer_count=$(systemctl list-timers --no-pager 2>/dev/null | grep -c "\.timer" | tr -d ' ')
        if [[ $timer_count -gt 0 ]]; then
            log_message "INFO" "发现 $timer_count 个systemd定时器"
        fi
    fi
}

check_process_monitoring() {
    log_message "INFO" "检查进程监控..."

    # 检查与技能相关的进程
    local skill_processes=$(ps aux | grep -E "(web-search|scheduled-task|imap-smtp)" | grep -v grep | wc -l)
    if [[ $skill_processes -gt 0 ]]; then
        log_message "INFO" "发现 $skill_processes 个技能相关进程:"
        ps aux | grep -E "(web-search|scheduled-task|imap-smtp)" | grep -v grep | head -3 | while read process; do
            log_message "INFO" "  $(echo "$process" | awk '{print $11 " " $12}')"
        done
    else
        log_message "INFO" "未发现技能相关进程运行"
    fi
}

generate_security_report() {
    log_message "INFO" "生成安全报告..."

    local report_file="/workspace/project/security-report-$(date +%Y%m%d-%H%M%S).txt"

    cat > "$report_file" << EOF
==========================================
LobsterAI 技能安全报告
生成时间: $(date '+%Y-%m-%d %H:%M:%S')
系统: $(uname -a)
==========================================

1. 系统概览
   主机名: $(hostname)
   用户: $(whoami)
   技能目录: $SKILLS_DIR
   技能数量: $(ls -1 "$SKILLS_DIR" | wc -l)

2. 权限检查
   目录权限: $(stat -c "%a" "$SKILLS_DIR")
   目录所有者: $(stat -c "%U:%G" "$SKILLS_DIR")
   setuid/setgid文件: $(find "$SKILLS_DIR" -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | wc -l) 个

3. 脚本安全检查
   危险模式检测: 已完成
   可疑文件: $(find "$SKILLS_DIR" -type f \( -name "*.sh" -o -name "*.py" -o -name "*.js" \) -exec grep -l "rm.*-rf\|chmod.*777\|wget.*http.*\\|.*sh\|curl.*http.*\\|.*sh\|bash.*<.*\\(" {} \; 2>/dev/null | wc -l) 个

4. 网络访问
   web-search服务器: $(ps aux | grep -q "web-search.*server" && echo "运行中" || echo "未运行")
   网络连接数: $(netstat -tunap 2>/dev/null | grep -E "(ESTABLISHED|LISTEN)" | grep -v "127.0.0.1" | wc -l) 个

5. 文件操作
   最近修改文件: $(find "$SKILLS_DIR" -type f -mtime -1 2>/dev/null | wc -l) 个

6. 定时任务
   Cron任务: $(crontab -l 2>/dev/null | grep -c -v "^#" | tr -d ' ') 个

7. 进程监控
   技能相关进程: $(ps aux | grep -E "(web-search|scheduled-task|imap-smtp)" | grep -v grep | wc -l) 个

8. 建议
   - 定期运行安全监控
   - 审查新安装的技能
   - 限制网络访问权限
   - 备份重要数据

==========================================
报告结束
EOF

    log_message "SUCCESS" "安全报告已生成: $report_file"
    echo ""
    echo "安全报告摘要:"
    tail -20 "$report_file"
}

main() {
    echo ""
    echo "=========================================="
    echo "  LobsterAI 技能安全监控系统 v1.0.0"
    echo "  开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="
    echo ""

    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"

    # 执行各项检查
    check_permissions
    echo ""

    check_script_safety
    echo ""

    check_network_access
    echo ""

    check_file_operations
    echo ""

    check_scheduled_tasks
    echo ""

    check_process_monitoring
    echo ""

    # 生成报告
    generate_security_report

    echo ""
    echo "=========================================="
    echo "  安全监控完成"
    echo "  日志文件: $LOG_FILE"
    echo "=========================================="
}

# 执行主函数
main "$@"