#!/bin/bash
# Self-Improving Agent 内存目录设置脚本
# 用于在sandbox环境中配置技能

echo "========================================="
echo "Self-Improving Agent 内存目录设置"
echo "========================================="

# 项目内存目录
PROJECT_MEMORY_DIR="/workspace/project/self-improving"

echo -e "\n📁 检查当前内存目录状态..."

# 检查是否已存在
if [ -d "$PROJECT_MEMORY_DIR" ]; then
    echo "✅ 内存目录已存在: $PROJECT_MEMORY_DIR"
    echo "   目录内容:"
    ls -la "$PROJECT_MEMORY_DIR/"
else
    echo "❌ 内存目录不存在，正在创建..."
    mkdir -p "$PROJECT_MEMORY_DIR"/{projects,domains,archive}
    echo "✅ 目录结构创建完成"
fi

# 初始化核心文件
echo -e "\n📄 初始化核心文件..."

# memory.md
if [ ! -f "$PROJECT_MEMORY_DIR/memory.md" ]; then
    cat > "$PROJECT_MEMORY_DIR/memory.md" << 'EOF'
# Memory (HOT Tier)

## Preferences
<!-- User preferences confirmed through usage -->

## Patterns
<!-- Observed patterns (3+ occurrences) -->

## Rules
<!-- Confirmed rules from corrections -->
EOF
    echo "✅ memory.md 已创建"
else
    echo "✅ memory.md 已存在"
fi

# corrections.md
if [ ! -f "$PROJECT_MEMORY_DIR/corrections.md" ]; then
    cat > "$PROJECT_MEMORY_DIR/corrections.md" << 'EOF'
# Corrections Log

| Date | What I Got Wrong | Correct Answer | Status |
|------|-----------------|----------------|--------|
EOF
    echo "✅ corrections.md 已创建"
else
    echo "✅ corrections.md 已存在"
fi

# index.md
if [ ! -f "$PROJECT_MEMORY_DIR/index.md" ]; then
    cat > "$PROJECT_MEMORY_DIR/index.md" << EOF
# Memory Index

| File | Lines | Last Updated |
|------|-------|--------------|
| memory.md | $(wc -l < "$PROJECT_MEMORY_DIR/memory.md" 2>/dev/null || echo "0") | $(date +'%Y-%m-%d %H:%M:%S') |
| corrections.md | $(wc -l < "$PROJECT_MEMORY_DIR/corrections.md" 2>/dev/null || echo "0") | $(date +'%Y-%m-%d %H:%M:%S') |
EOF
    echo "✅ index.md 已创建"
else
    echo "✅ index.md 已存在"
fi

# 创建使用说明
echo -e "\n📋 使用说明:"
cat > "$PROJECT_MEMORY_DIR/usage.md" << 'EOF'
# Self-Improving Agent 使用说明 (Sandbox环境)

## 目录结构
内存目录已设置在: `/workspace/project/self-improving/`

## 核心文件
1. `memory.md` - HOT层内存（始终加载）
2. `corrections.md` - 纠正日志（最近50条）
3. `index.md` - 内存索引
4. `projects/` - 项目特定学习
5. `domains/` - 领域特定知识
6. `archive/` - 冷存储（衰减模式）

## 在Sandbox中使用
由于sandbox限制，技能无法访问 `~/self-improving/`。
请手动引用项目目录中的内存文件。

## 手动操作示例
1. 查看内存: `cat /workspace/project/self-improving/memory.md`
2. 添加纠正: 手动编辑 corrections.md
3. 查看索引: `cat /workspace/project/self-improving/index.md`

## 技能触发时机
- 用户纠正时 ("不，那是错的...")
- 发现重复模式时
- 完成重要工作后自我评估
EOF

echo "✅ usage.md 使用说明已创建"

echo -e "\n🔧 环境设置建议:"
echo "由于sandbox限制，建议:"
echo "1. 在需要时手动引用: /workspace/project/self-improving/"
echo "2. 或设置别名: alias simemory='cd /workspace/project/self-improving'"
echo "3. 技能的核心逻辑仍然可以通过阅读技能文档来应用"

echo -e "\n📊 最终状态:"
echo "内存目录: $PROJECT_MEMORY_DIR"
echo "总文件数: $(find "$PROJECT_MEMORY_DIR" -type f | wc -l)"
echo "目录大小: $(du -sh "$PROJECT_MEMORY_DIR" | cut -f1)"

echo -e "\n========================================="
echo "设置完成! Self-Improving Agent 内存目录已就绪"
echo "路径: [self-improving](file:///workspace/project/self-improving)"
echo "========================================="