#!/usr/bin/env python3
"""
最终确认TAVILY_API_KEY状态
"""

import os
import sys

print("=" * 60)
print("TAVILY_API_KEY 最终状态确认")
print("=" * 60)

# 获取所有环境变量
all_env_vars = dict(os.environ)

# 检查TAVILY_API_KEY
tavily_key = all_env_vars.get('TAVILY_API_KEY')

print(f"\n📊 检查结果:")
print(f"   1. TAVILY_API_KEY存在: {'是' if 'TAVILY_API_KEY' in all_env_vars else '否'}")
print(f"   2. TAVILY_API_KEY值: {repr(tavily_key)}")
print(f"   3. 类型: {type(tavily_key)}")
print(f"   4. 是否为None: {tavily_key is None}")
print(f"   5. 是否为空字符串: {tavily_key == ''}")
print(f"   6. 长度: {len(tavily_key) if tavily_key else 0}")

# 检查其他相关API Key
print(f"\n🔍 检查其他API Key:")
api_keys_to_check = ['TAVILY_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'BRAVE_API_KEY']
for key in api_keys_to_check:
    value = all_env_vars.get(key)
    if value:
        print(f"   {key}: 已设置 (长度: {len(value)})")
    else:
        print(f"   {key}: 未设置")

# 结论
print(f"\n✅ 最终结论:")
if tavily_key and len(tavily_key) > 10:
    print(f"   TAVILY_API_KEY 已正确设置，长度为 {len(tavily_key)} 字符")
    print(f"   前10字符: {tavily_key[:10]}...")
elif tavily_key == '':
    print(f"   TAVILY_API_KEY 设置为空字符串")
else:
    print(f"   TAVILY_API_KEY 未设置 (值为 None)")

print(f"\n💡 建议:")
if not tavily_key:
    print(f"   1. 需要设置TAVILY_API_KEY环境变量才能使用Tavily搜索功能")
    print(f"   2. 可以使用命令: export TAVILY_API_KEY='your_api_key_here'")
    print(f"   3. 或者创建.env文件并设置变量")
    print(f"   4. 目前只能使用RSS源功能")

print(f"\n" + "=" * 60)