#!/usr/bin/env python3
"""
测试单只股票的技术分析
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.technical_agent import TechnicalAnalysisAgent

if __name__ == "__main__":
    print("=== 单只股票技术分析测试 ===")
    
    # 创建技术分析Agent实例
    agent = TechnicalAnalysisAgent()
    
    # 测试一只股票，例如信维通信(300136)
    test_stock = {"code": "300136", "name": "信维通信"}
    
    print(f"测试股票: {test_stock['code']} {test_stock['name']}")
    print("开始分析...")
    
    # 分析股票
    result = agent.analyze_stock(test_stock)
    
    # 打印分析结果
    print("\n分析结果:")
    print(f"股票代码: {result['code']}")
    print(f"股票名称: {result['name']}")
    print(f"当前价格: {result['price']:.2f}")
    print(f"涨跌幅: {result['change_percent']:+.2f}%")
    print(f"综合评分: {result['score']:.1f}/10")
    print(f"操作信号: {result['signal']}")
    
    print("\n技术指标:")
    indicators = result['indicators']
    for key, value in indicators.items():
        print(f"- {key}: {value}")
    
    print("\n测试完成！")
