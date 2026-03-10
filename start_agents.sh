#!/bin/bash

# 多Agent炒股系统启动脚本
# 支持钉钉通知集成

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
CONFIG_DIR="$PROJECT_DIR/config"
AGENTS_DIR="$PROJECT_DIR/agents"

# 创建目录
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

# 检查依赖
check_dependencies() {
    log "检查系统依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3未安装"
        return 1
    fi

    log "依赖检查完成 - 注意: 在受保护环境中，psutil和requests可能不可用"
}

# 加载钉钉配置
load_dingtalk_config() {
    local config_file="$CONFIG_DIR/dingtalk.json"

    if [[ ! -f "$config_file" ]]; then
        log "钉钉配置文件不存在: $config_file"
        return 1
    fi

    # 检查是否启用钉钉
    if grep -q '"enabled": true' "$config_file" 2>/dev/null; then
        log "钉钉通知已启用"
        return 0
    else
        log "钉钉通知已禁用"
        return 1
    fi
}

# 发送钉钉启动通知
send_start_notification() {
    log "发送系统启动通知..."

    if load_dingtalk_config; then
        python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from dingtalk import DingTalkSender
    sender = DingTalkSender('config/dingtalk.json')
    if sender:
        message = '多Agent炒股系统启动完成'
        sender.send_message(message, title='系统启动通知', level='info')
        print('钉钉启动通知发送成功')
    else:
        print('钉钉通知器初始化失败')
except Exception as e:
    print(f'钉钉通知发送失败: {e}')
"
    else
        log "钉钉通知未启用，跳过启动通知"
    fi
}

# 启动监控Agent
start_monitor_agent() {
    log "启动监控Agent..."

    local monitor_script="$AGENTS_DIR/monitor_agent.py"
    local config_file="$CONFIG_DIR/monitor_config.json"

    if [[ ! -f "$monitor_script" ]]; then
        log_error "监控Agent脚本不存在: $monitor_script"
        return 1
    fi

    if [[ ! -f "$config_file" ]]; then
        log_error "监控配置文件不存在: $config_file"
        return 1
    fi

    # 启动监控Agent
    nohup python3 "$monitor_script" --config "$config_file" --start --daemon > "$LOG_DIR/monitor.log" 2>&1 &
    local pid=$!

    echo "$pid" > "$LOG_DIR/monitor.pid"
    log "监控Agent已启动 (PID: $pid)"

    # 等待监控Agent初始化
    sleep 3

    # 检查是否运行 (使用kill -0兼容BusyBox)
    if kill -0 "$pid" 2>/dev/null; then
        log "监控Agent运行正常"
        return 0
    else
        log_error "监控Agent启动失败，请查看日志: $LOG_DIR/monitor.log"
        return 1
    fi
}

# 停止监控Agent
stop_monitor_agent() {
    log "停止监控Agent..."

    local pid_file="$LOG_DIR/monitor.pid"

    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")

        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log "已发送停止信号给监控Agent (PID: $pid)"

            # 等待进程停止
            for i in {1..10}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    log "监控Agent已停止"
                    rm -f "$pid_file"
                    return 0
                fi
                sleep 1
            done

            log_error "监控Agent未在10秒内停止，尝试强制停止"
            kill -9 "$pid" 2>/dev/null
            rm -f "$pid_file"
        else
            log "监控Agent未在运行"
            rm -f "$pid_file"
        fi
    else
        log "监控Agent PID文件不存在，可能未在运行"
    fi

    # 发送停止通知
    if load_dingtalk_config; then
        python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from dingtalk import DingTalkSender
    sender = DingTalkSender('config/dingtalk.json')
    if sender:
        message = '多Agent炒股系统已停止'
        sender.send_message(message, title='系统停止通知', level='info')
        print('钉钉停止通知发送成功')
except Exception as e:
    print(f'钉钉通知发送失败: {e}')
"
    fi

    return 0
}

# 停止其他Agent
stop_other_agents() {
    log "停止其他Agent..."

    # 停止数据采集Agent
    local data_pid_file="$LOG_DIR/data_agent.pid"
    if [[ -f "$data_pid_file" ]]; then
        local pid=$(cat "$data_pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log "已发送停止信号给数据采集Agent (PID: $pid)"
            # 等待进程停止
            for i in {1..5}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    log "数据采集Agent已停止"
                    break
                fi
                sleep 1
            done
        else
            log "数据采集Agent未在运行"
        fi
        rm -f "$data_pid_file"
    else
        log "数据采集Agent PID文件不存在"
    fi

    # 停止技术分析Agent
    local technical_pid_file="$LOG_DIR/technical_agent.pid"
    if [[ -f "$technical_pid_file" ]]; then
        local pid=$(cat "$technical_pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log "已发送停止信号给技术分析Agent (PID: $pid)"
            # 等待进程停止
            for i in {1..5}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    log "技术分析Agent已停止"
                    break
                fi
                sleep 1
            done
        else
            log "技术分析Agent未在运行"
        fi
        rm -f "$technical_pid_file"
    else
        log "技术分析Agent PID文件不存在"
    fi

    log "其他Agent停止完成"
}

# 启动其他Agent
start_other_agents() {
    log "启动其他Agent..."

    # 启动数据采集Agent
    log "启动数据采集Agent..."
    nohup python3 "$AGENTS_DIR/data_agent.py" > "$LOG_DIR/data_agent.log" 2>&1 &
    echo $! > "$LOG_DIR/data_agent.pid"
    log "数据采集Agent已启动 (PID: $!)"

    # 启动技术分析Agent
    log "启动技术分析Agent..."
    nohup python3 "$AGENTS_DIR/technical_agent.py" > "$LOG_DIR/technical_agent.log" 2>&1 &
    echo $! > "$LOG_DIR/technical_agent.pid"
    log "技术分析Agent已启动 (PID: $!)"

    log "其他Agent启动完成"
}

# 检查系统状态
check_system_status() {
    log "检查系统状态..."

    # 检查监控Agent
    local pid_file="$LOG_DIR/monitor.pid"

    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")

        if kill -0 "$pid" 2>/dev/null; then
            log "✓ 监控Agent: 运行中 (PID: $pid)"
        else
            log "✗ 监控Agent: 未运行"
        fi
    else
        log "✗ 监控Agent: 未运行"
    fi

    # 检查日志目录
    if [[ -d "$LOG_DIR" ]]; then
        local log_count=$(find "$LOG_DIR" -name "*.log" -type f | wc -l)
        log "✓ 日志目录: 正常 ($log_count 个日志文件)"
    else
        log "✗ 日志目录: 不存在"
    fi

    # 检查配置文件
    local config_files=("dingtalk.json" "monitor_config.json")
    local missing_configs=()

    for config in "${config_files[@]}"; do
        if [[ ! -f "$CONFIG_DIR/$config" ]]; then
            missing_configs+=("$config")
        fi
    done

    if [[ ${#missing_configs[@]} -eq 0 ]]; then
        log "✓ 配置文件: 完整"
    else
        log "✗ 配置文件缺失: ${missing_configs[*]}"
    fi

    log "系统状态检查完成"
}

# 主函数
main() {
    local action="${1:-help}"

    case "$action" in
        start)
            log "启动多Agent炒股系统..."
            check_dependencies
            send_start_notification
            start_monitor_agent
            start_other_agents
            check_system_status
            log "系统启动完成"
            ;;
        stop)
            log "停止多Agent炒股系统..."
            stop_other_agents
            stop_monitor_agent
            log "系统停止完成"
            ;;
        restart)
            log "重启多Agent炒股系统..."
            stop_other_agents
            stop_monitor_agent
            sleep 2
            send_start_notification
            start_monitor_agent
            start_other_agents
            log "系统重启完成"
            ;;
        status)
            check_system_status
            ;;
        test-dingtalk)
            log "测试钉钉通知..."
            if load_dingtalk_config; then
                python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from dingtalk import DingTalkSender
    sender = DingTalkSender('config/dingtalk.json')
    if sender:
        message = '钉钉连接测试成功'
        sender.send_message(message, title='测试通知', level='info')
        print('钉钉连接测试成功')
    else:
        print('钉钉通知器初始化失败')
except Exception as e:
    print(f'钉钉测试异常: {e}')
"
            else
                log "钉钉通知未启用"
            fi
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|test-dingtalk}"
            echo ""
            echo "命令:"
            echo "  start         启动系统"
            echo "  stop          停止系统"
            echo "  restart       重启系统"
            echo "  status        查看系统状态"
            echo "  test-dingtalk 测试钉钉通知"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"