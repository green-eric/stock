#!/bin/bash
# Self-Improving Agent 工具脚本
# 提供简单的命令来管理技能

SI_HOME="/workspace/project"
SI_MEMORY="$SI_HOME/self-improving"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 帮助函数
show_help() {
    echo -e "${BLUE}Self-Improving Agent 工具${NC}"
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启用Self-Improving Agent (设置HOME)"
    echo "  stop      恢复原始HOME"
    echo "  status    显示当前状态"
    echo "  memory    查看内存内容"
    echo "  corrections 查看纠正记录"
    echo "  add-error 添加错误记录"
    echo "  add-learning 添加学习记录"
    echo "  help      显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0 start      # 启用技能"
    echo "  $0 memory     # 查看内存"
    echo "  $0 status     # 检查状态"
}

# 状态检查
check_status() {
    echo -e "${BLUE}=== Self-Improving Agent 状态 ===${NC}"
    echo -e "当前HOME: ${GREEN}$HOME${NC}"

    if [ "$HOME" = "$SI_HOME" ]; then
        echo -e "技能状态: ${GREEN}已启用${NC}"
    else
        echo -e "技能状态: ${YELLOW}未启用${NC}"
        echo "提示: 使用 '$0 start' 启用技能"
    fi

    if [ -d "$SI_MEMORY" ]; then
        echo -e "内存目录: ${GREEN}$SI_MEMORY${NC}"
        echo "目录内容:"
        ls -la "$SI_MEMORY/" | tail -n +2
    else
        echo -e "内存目录: ${RED}不存在${NC}"
        echo "提示: 请先运行 setup_self_improving.sh"
    fi
}

# 启用技能
start_si() {
    export HOME="$SI_HOME"
    echo -e "${GREEN}✅ Self-Improving Agent 已启用${NC}"
    echo "HOME 设置为: $HOME"
    echo "技能现在可以访问 ~/self-improving/"
    check_status
}

# 停止技能
stop_si() {
    export HOME="/root"
    echo -e "${YELLOW}🔄 恢复原始HOME${NC}"
    echo "HOME 恢复为: $HOME"
}

# 查看内存
show_memory() {
    if [ -f "$SI_MEMORY/memory.md" ]; then
        echo -e "${BLUE}=== 内存内容 (memory.md) ===${NC}"
        cat "$SI_MEMORY/memory.md"
    else
        echo -e "${RED}❌ memory.md 不存在${NC}"
    fi
}

# 查看纠正记录
show_corrections() {
    if [ -f "$SI_MEMORY/corrections.md" ]; then
        echo -e "${BLUE}=== 纠正记录 (corrections.md) ===${NC}"
        cat "$SI_MEMORY/corrections.md"
    else
        echo -e "${RED}❌ corrections.md 不存在${NC}"
    fi
}

# 添加错误记录
add_error() {
    if [ "$HOME" != "$SI_HOME" ]; then
        echo -e "${YELLOW}⚠️  请先启用技能: $0 start${NC}"
        return 1
    fi

    echo -e "${BLUE}添加错误记录${NC}"
    read -p "错误描述: " error_desc
    read -p "命令/操作: " error_cmd
    read -p "错误信息: " error_msg
    read -p "解决方案: " error_solution

    timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    error_entry="## 错误记录 - $timestamp
- **描述**: $error_desc
- **命令**: \`$error_cmd\`
- **错误信息**: $error_msg
- **解决方案**: $error_solution
- **状态**: ⚠️ 待解决
"

    echo -e "\n$error_entry" >> "$SI_MEMORY/corrections.md"
    echo -e "${GREEN}✅ 错误记录已添加${NC}"
}

# 添加学习记录
add_learning() {
    if [ "$HOME" != "$SI_HOME" ]; then
        echo -e "${YELLOW}⚠️  请先启用技能: $0 start${NC}"
        return 1
    fi

    echo -e "${BLUE}添加学习记录${NC}"
    read -p "学习内容: " learning_content
    read -p "类别 (best_practice/correction/knowledge_gap): " learning_category
    read -p "上下文: " learning_context
    read -p "优先级 (高/中/低): " learning_priority

    timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    learning_entry="## 学习记录 - $timestamp
- **类别**: $learning_category
- **内容**: $learning_content
- **上下文**: $learning_context
- **优先级**: $learning_priority
- **状态**: ✅ 已学习
"

    # 添加到学习文件（如果存在）或创建新文件
    if [ -f "$SI_MEMORY/../.learnings/LEARNINGS.md" ]; then
        echo -e "\n$learning_entry" >> "$SI_MEMORY/../.learnings/LEARNINGS.md"
        echo -e "${GREEN}✅ 学习记录已添加到 .learnings/LEARNINGS.md${NC}"
    else
        echo -e "\n$learning_entry" >> "$SI_MEMORY/learning.md"
        echo -e "${GREEN}✅ 学习记录已添加到 learning.md${NC}"
    fi
}

# 主逻辑
case "$1" in
    start)
        start_si
        ;;
    stop)
        stop_si
        ;;
    status)
        check_status
        ;;
    memory)
        show_memory
        ;;
    corrections)
        show_corrections
        ;;
    add-error)
        add_error
        ;;
    add-learning)
        add_learning
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}未知命令: $1${NC}"
        echo "使用 '$0 help' 查看可用命令"
        ;;
esac