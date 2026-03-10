#!/bin/bash
# Self-Improving Agent 启动脚本
# 解决sandbox环境中 ~/self-improving/ 路径问题

echo "========================================="
echo "Self-Improving Agent 启动脚本"
echo "========================================="

# 保存原始HOME
ORIGINAL_HOME="$HOME"
PROJECT_HOME="/workspace/project"

echo -e "\n🔧 环境设置:"
echo "   原始HOME: $ORIGINAL_HOME"
echo "   项目HOME: $PROJECT_HOME"

# 设置HOME到项目目录
export HOME="$PROJECT_HOME"
echo "   当前HOME: $HOME"

# 检查内存目录
MEMORY_DIR="$HOME/self-improving"
echo -e "\n📁 内存目录检查:"
if [ -d "$MEMORY_DIR" ]; then
    echo "   ✅ 内存目录存在: $MEMORY_DIR"
    echo "   目录内容:"
    ls -la "$MEMORY_DIR/"

    # 检查核心文件
    echo -e "\n📄 核心文件状态:"
    for file in "memory.md" "corrections.md" "index.md"; do
        if [ -f "$MEMORY_DIR/$file" ]; then
            lines=$(wc -l < "$MEMORY_DIR/$file")
            echo "   ✅ $file: $lines 行"
        else
            echo "   ❌ $file: 不存在"
        fi
    done
else
    echo "   ❌ 内存目录不存在，请先运行 setup_self_improving.sh"
    exit 1
fi

# 检查技能目录
SKILL_DIR="/workspace/project/SKILLs/lobsterai-skill-zip-VnOv98"
echo -e "\n🧠 技能目录检查:"
if [ -d "$SKILL_DIR" ]; then
    echo "   ✅ 技能目录存在: $SKILL_DIR"

    # 检查技能文档
    if [ -f "$SKILL_DIR/skill.md" ]; then
        skill_name=$(grep -m1 "^name:" "$SKILL_DIR/skill.md" | cut -d: -f2 | tr -d ' ')
        version=$(grep -m1 "^version:" "$SKILL_DIR/skill.md" | cut -d: -f2 | tr -d ' ')
        echo "   技能名称: $skill_name"
        echo "   版本: $version"
    fi
else
    echo "   ❌ 技能目录不存在"
fi

# 测试技能功能
echo -e "\n🚀 测试技能功能:"

# 测试1: 检查是否可以访问内存文件
echo "   1. 测试内存文件访问..."
if [ -f "$MEMORY_DIR/memory.md" ]; then
    memory_content=$(head -5 "$MEMORY_DIR/memory.md")
    echo "      ✅ 可以访问 memory.md"
    echo "      内容预览:"
    echo "      $memory_content" | sed 's/^/      /'
else
    echo "      ❌ 无法访问 memory.md"
fi

# 测试2: 模拟纠正记录
echo -e "\n   2. 模拟纠正记录..."
CORRECTIONS_FILE="$MEMORY_DIR/corrections.md"
if [ -f "$CORRECTIONS_FILE" ]; then
    # 添加测试记录
    timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    test_record="| $timestamp | 路径测试错误 | 使用HOME=$PROJECT_HOME | ✅ 测试通过 |"

    # 检查是否已有表头
    if grep -q "What I Got Wrong" "$CORRECTIONS_FILE"; then
        # 在表头后添加记录
        sed -i '/What I Got Wrong/a '"$test_record" "$CORRECTIONS_FILE"
        echo "      ✅ 成功添加测试纠正记录"
    else
        echo "      ⚠️ 纠正文件格式不标准"
    fi

    # 显示最新记录
    echo "      最新纠正记录:"
    tail -3 "$CORRECTIONS_FILE" | sed 's/^/      /'
else
    echo "      ❌ 无法访问 corrections.md"
fi

# 测试3: 检查索引更新
echo -e "\n   3. 检查索引更新..."
INDEX_FILE="$MEMORY_DIR/index.md"
if [ -f "$INDEX_FILE" ]; then
    # 更新索引中的时间戳
    sed -i "s/| memory.md |.*|/| memory.md | $(wc -l < "$MEMORY_DIR/memory.md") | $timestamp |/" "$INDEX_FILE"
    sed -i "s/| corrections.md |.*|/| corrections.md | $(wc -l < "$MEMORY_DIR/corrections.md") | $timestamp |/" "$INDEX_FILE"
    echo "      ✅ 索引已更新"
    echo "      索引内容:"
    cat "$INDEX_FILE" | sed 's/^/      /'
else
    echo "      ❌ 无法访问 index.md"
fi

# 使用说明
echo -e "\n💡 使用说明:"
echo "   1. 要使用Self-Improving Agent技能，需要设置HOME环境变量:"
echo "      export HOME='/workspace/project'"
echo "   2. 或者直接使用此脚本启动: ./start_self_improving.sh"
echo "   3. 技能现在可以正常访问 ~/self-improving/ 目录"
echo "   4. 内存目录: [self-improving](file:///workspace/project/self-improving)"

# 创建别名建议
echo -e "\n🔧 建议的bash别名:"
echo "   添加到 ~/.bashrc 或当前shell会话:"
echo "   alias si-start='export HOME=\"/workspace/project\" && echo \"Self-Improving Agent已启用\"'"
echo "   alias si-stop='export HOME=\"$ORIGINAL_HOME\" && echo \"恢复原始HOME\"'"
echo "   alias si-status='echo \"当前HOME: \$HOME\" && ls -la ~/self-improving/ 2>/dev/null || echo \"内存目录不存在\"'"

# 恢复原始HOME（可选）
# export HOME="$ORIGINAL_HOME"

echo -e "\n========================================="
echo "启动完成! Self-Improving Agent 已就绪"
echo "当前HOME: $HOME"
echo "内存目录: ~/self-improving/ → $MEMORY_DIR"
echo "========================================="

echo -e "\n📋 下一步:"
echo "   1. 技能现在可以正常使用 ~/self-improving/ 路径"
echo "   2. 当用户纠正时，技能会自动记录到 corrections.md"
echo "   3. 定期查看 memory.md 和 corrections.md 学习"
echo "   4. 使用 'si-status' 检查状态"