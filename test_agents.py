#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试代理通信
"""

import time
from agents.data_agent import DataCollectorAgent
from agents.technical_agent import TechnicalAnalysisAgent
from data.data_share import data_share


def test_data_agent():
    """测试数据采集Agent"""
    print("\n=== 测试数据采集Agent ===")
    
    # 创建数据采集Agent实例
    data_agent = DataCollectorAgent(use_real_data=False)  # 使用模拟数据以确保测试稳定
    
    # 测试收集市场数据
    print("收集市场数据...")
    market_data = data_agent.collect_market_data()
    print(f"收集到的市场数据: {market_data}")
    
    # 验证数据结构
    assert market_data is not None, "市场数据为空"
    assert 'timestamp' in market_data, "市场数据缺少timestamp字段"
    assert 'hot_sectors' in market_data, "市场数据缺少hot_sectors字段"
    assert 'capital_flow' in market_data, "市场数据缺少capital_flow字段"
    
    # 验证热点板块数据
    assert isinstance(market_data['hot_sectors'], list), "热点板块应该是列表"
    if market_data['hot_sectors']:
        sector = market_data['hot_sectors'][0]
        assert 'name' in sector, "板块数据缺少name字段"
        assert 'change' in sector, "板块数据缺少change字段"
        assert 'leader' in sector, "板块数据缺少leader字段"
    
    # 验证资金流向数据
    assert isinstance(market_data['capital_flow'], dict), "资金流向应该是字典"
    assert 'northbound_in' in market_data['capital_flow'], "资金流向缺少northbound_in字段"
    assert 'main_net_in' in market_data['capital_flow'], "资金流向缺少main_net_in字段"
    assert 'retail_net_in' in market_data['capital_flow'], "资金流向缺少retail_net_in字段"
    
    # 测试数据是否被正确存储到data_share
    stored_market_data = data_share.get_market_data()
    print(f"存储到data_share的市场数据: {stored_market_data}")
    assert stored_market_data is not None, "市场数据未存储到data_share"
    
    print("数据采集Agent测试通过!")


def test_technical_agent():
    """测试技术分析Agent"""
    print("\n=== 测试技术分析Agent ===")
    
    # 创建技术分析Agent实例
    technical_agent = TechnicalAnalysisAgent()
    
    # 测试加载监控列表
    watch_list = technical_agent.watch_list
    print(f"加载的监控列表: {watch_list}")
    assert len(watch_list) > 0, "监控列表为空"
    
    # 测试分析单只股票
    print("分析单只股票...")
    stock = watch_list[0]
    analysis_result = technical_agent.analyze_stock(stock)
    print(f"股票分析结果: {analysis_result}")
    
    # 验证分析结果结构
    assert analysis_result is not None, "分析结果为空"
    assert 'code' in analysis_result, "分析结果缺少code字段"
    assert 'name' in analysis_result, "分析结果缺少name字段"
    assert 'price' in analysis_result, "分析结果缺少price字段"
    assert 'change_percent' in analysis_result, "分析结果缺少change_percent字段"
    assert 'indicators' in analysis_result, "分析结果缺少indicators字段"
    assert 'score' in analysis_result, "分析结果缺少score字段"
    assert 'signal' in analysis_result, "分析结果缺少signal字段"
    
    # 验证技术指标结构
    indicators = analysis_result['indicators']
    assert 'macd' in indicators, "技术指标缺少macd字段"
    assert 'kdj' in indicators, "技术指标缺少kdj字段"
    assert 'rsi' in indicators, "技术指标缺少rsi字段"
    assert 'volume_ratio' in indicators, "技术指标缺少volume_ratio字段"
    assert 'ma5' in indicators, "技术指标缺少ma5字段"
    assert 'ma10' in indicators, "技术指标缺少ma10字段"
    assert 'ma20' in indicators, "技术指标缺少ma20字段"
    
    # 测试发送分析结果
    print("发送分析结果...")
    buy_count = technical_agent.send_analysis_results()
    print(f"发现的买入信号数量: {buy_count}")
    
    # 测试数据是否被正确存储到data_share
    stored_analysis = data_share.get_analysis_results()
    print(f"存储到data_share的分析结果: {stored_analysis}")
    assert stored_analysis is not None, "分析结果未存储到data_share"
    
    print("技术分析Agent测试通过!")


def test_agent_integration():
    """测试代理集成"""
    print("\n=== 测试代理集成 ===")
    
    # 创建数据采集Agent
    data_agent = DataCollectorAgent(use_real_data=False)
    
    # 创建技术分析Agent
    technical_agent = TechnicalAnalysisAgent()
    
    # 测试数据采集和技术分析的协同工作
    print("测试数据采集和技术分析协同工作...")
    
    # 1. 采集市场数据
    market_data = data_agent.collect_market_data()
    print(f"采集到市场数据: {market_data}")
    
    # 2. 分析股票
    watch_list = technical_agent.watch_list
    analysis_results = []
    for stock in watch_list[:2]:  # 只分析前2只股票以节省时间
        result = technical_agent.analyze_stock(stock)
        analysis_results.append(result)
        print(f"分析股票 {stock['code']} {stock['name']}: {result['signal']} (评分: {result['score']:.1f})")
    
    # 3. 发送分析结果
    buy_count = technical_agent.send_analysis_results()
    print(f"发送分析结果，发现 {buy_count} 个买入信号")
    
    # 4. 验证数据共享
    stored_market_data = data_share.get_market_data()
    stored_analysis = data_share.get_analysis_results()
    
    assert stored_market_data is not None, "市场数据未共享"
    assert stored_analysis is not None, "分析结果未共享"
    
    print("代理集成测试通过!")


if __name__ == "__main__":
    print("开始测试代理通信...")
    
    try:
        test_data_agent()
        test_technical_agent()
        test_agent_integration()
        print("\n✅ 所有代理通信测试通过!")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
