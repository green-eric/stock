#!/usr/bin/env python3
"""
测试钉钉消息发送功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.technical_agent import TechnicalAnalysisAgent

if __name__ == "__main__":
    print("=== 测试钉钉消息发送功能 ===")
    
    # 创建技术分析Agent实例
    agent = TechnicalAnalysisAgent()
    
    print(f"监控股票数量: {len(agent.watch_list)}")
    print("开始分析股票...")
    
    # 运行分析并发送结果
    buy_count = agent.send_analysis_results()
    
    print(f"\n=== 分析完成 ===")
    print(f"发现买入信号: {buy_count} 个")
    
    # 显示钉钉消息格式
    print("\n=== 钉钉消息格式预览 ===")
    print("如果有买入信号，将发送以下格式的消息：")
    print("\n🚨 买入信号: 股票代码 股票名称")
    print("\n💰 价格信息:")
    print("- 当前价: ¥价格")
    print("- 涨跌幅: 涨跌幅%")
    print("\n🎯 操作建议:")
    print("- 建议仓位: 5-10%")
    print("- 持仓期: 1-3天")
    print("- 止损位: 当前价 × 0.92")
    print("\n⏰ 分析时间: 时间")
    
    print("\n以上是将要发送到钉钉的信息格式")
