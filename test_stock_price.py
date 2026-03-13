#!/usr/bin/env python3
"""
测试股票价格取数功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.technical_agent import TechnicalAnalysisAgent

if __name__ == "__main__":
    print("=== 股票价格取数测试 ===")
    
    # 创建技术分析Agent实例
    agent = TechnicalAnalysisAgent()
    
    # 测试股票列表
    test_stocks = [
        {"code": "000035", "name": "中国天楹"},
        {"code": "600487", "name": "亨通光电"}
    ]
    
    print(f"测试股票数量: {len(test_stocks)}")
    print("开始测试股票价格取数...\n")
    
    for stock in test_stocks:
        code = stock["code"]
        name = stock["name"]
        
        print(f"测试股票: {code} {name}")
        
        # 测试从多个数据源获取价格
        price = agent._get_stock_price_from_multiple_sources(code)
        
        if price:
            print(f"✓ 成功获取价格: ¥{price:.2f}")
        else:
            print("✗ 无法获取价格，使用默认值")
        
        # 测试单独从每个数据源获取价格
        for source in ['tushare', 'baostock']:
            source_price = agent._get_price_from_source(source, code)
            if source_price:
                print(f"  - {source}: ¥{source_price:.2f}")
            else:
                print(f"  - {source}: 失败")
        
        print()
    
    print("=== 测试完成 ===")
