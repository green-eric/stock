#!/usr/bin/env python3
"""
测试错误处理模块
"""

from utils.error_handler import error_handler

def test_error_handling():
    """测试错误处理机制"""
    print('错误处理器初始化成功')
    
    # 测试基本错误处理
    def test_func():
        raise ValueError('测试错误')
    
    result = error_handler.try_execute(test_func)
    print('测试错误处理成功，结果:', result)
    assert result is None, "错误处理应该返回None"
    
    # 测试错误统计
    stats = error_handler.get_error_stats()
    print('错误统计:', stats)
    assert 'ValueError' in stats, "错误统计应该包含ValueError"
    
    # 测试带回退函数的错误处理
    def fallback():
        return '回退值'
    
    def test_func_with_fallback():
        raise ConnectionError('测试连接错误')
    
    result_with_fallback = error_handler.try_execute_with_fallback(test_func_with_fallback, fallback)
    print('测试带回退函数的错误处理，结果:', result_with_fallback)
    assert result_with_fallback == '回退值', "带回退函数的错误处理应该返回回退值"
    
    # 测试错误统计
    stats = error_handler.get_error_stats()
    print('错误统计:', stats)
    assert 'ConnectionError' in stats, "错误统计应该包含ConnectionError"
    
    print('错误处理模块测试完成')