#!/usr/bin/env python3
"""
测试错误处理模块
"""

from utils.error_handler import error_handler

print('错误处理器初始化成功')

def test_func():
    raise ValueError('测试错误')

result = error_handler.try_execute(test_func)
print('测试错误处理成功，结果:', result)
print('错误统计:', error_handler.get_error_stats())

# 测试带回退函数的错误处理
def fallback():
    return '回退值'

def test_func_with_fallback():
    raise ConnectionError('测试连接错误')

result_with_fallback = error_handler.try_execute_with_fallback(test_func_with_fallback, fallback)
print('测试带回退函数的错误处理，结果:', result_with_fallback)
print('错误统计:', error_handler.get_error_stats())

print('错误处理模块测试完成')