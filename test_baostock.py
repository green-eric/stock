#!/usr/bin/env python3
"""
测试BaoStock数据源
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.technical_agent import TechnicalAnalysisAgent

if __name__ == "__main__":
    print("=== BaoStock数据源测试 ===")
    
    # 创建技术分析Agent实例
    agent = TechnicalAnalysisAgent()
    
    # 测试股票列表
    test_stocks = [
        {"code": "000035", "name": "中国天楹"},
        {"code": "600487", "name": "亨通光电"}
    ]
    
    print(f"测试股票数量: {len(test_stocks)}")
    print("开始测试BaoStock数据源...\n")
    
    for stock in test_stocks:
        code = stock["code"]
        name = stock["name"]
        
        print(f"测试股票: {code} {name}")
        
        # 直接测试BaoStock数据源
        price = agent._get_price_from_source('baostock', code)
        
        if price:
            print(f"✓ BaoStock成功获取价格: ¥{price:.2f}")
        else:
            print("✗ BaoStock获取价格失败")
        
        print()
    
    print("=== 测试完成 ===")
