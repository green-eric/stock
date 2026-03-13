#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多数据源功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.data_agent import DataCollectorAgent

def test_akshare_data_source():
    """测试AKShare数据源"""
    print("\n=== 测试AKShare数据源 ===")
    
    try:
        # 创建数据采集Agent，指定使用AKShare作为主数据源
        agent = DataCollectorAgent(primary_source='akshare')
        
        # 测试数据采集
        data = agent.collect_market_data()
        
        print(f"✓ AKShare数据源测试成功")
        print(f"  数据源: {data.get('data_source', '未知')}")
        print(f"  热点板块数量: {len(data.get('hot_sectors', []))}")
        print(f"  北向资金: {data.get('capital_flow', {}).get('northbound_in', 'N/A')}亿")
        print(f"  主力资金: {data.get('capital_flow', {}).get('main_net_in', 'N/A')}亿")
        
        return True
    except Exception as e:
        print(f"✗ AKShare数据源测试失败: {e}")
        return False

def test_sina_data_source():
    """测试新浪财经数据源"""
    print("\n=== 测试新浪财经数据源 ===")
    
    try:
        # 创建数据采集Agent，指定使用新浪财经作为主数据源
        agent = DataCollectorAgent(primary_source='sina')
        
        # 测试数据采集
        data = agent.collect_market_data()
        
        print(f"✓ 新浪财经数据源测试成功")
        print(f"  数据源: {data.get('data_source', '未知')}")
        print(f"  热点板块数量: {len(data.get('hot_sectors', []))}")
        print(f"  北向资金: {data.get('capital_flow', {}).get('northbound_in', 'N/A')}亿")
        print(f"  主力资金: {data.get('capital_flow', {}).get('main_net_in', 'N/A')}亿")
        
        return True
    except Exception as e:
        print(f"✗ 新浪财经数据源测试失败: {e}")
        return False

def test_eastmoney_data_source():
    """测试东方财富数据源"""
    print("\n=== 测试东方财富数据源 ===")
    
    try:
        # 创建数据采集Agent，指定使用东方财富作为主数据源
        agent = DataCollectorAgent(primary_source='eastmoney')
        
        # 测试数据采集
        data = agent.collect_market_data()
        
        print(f"✓ 东方财富数据源测试成功")
        print(f"  数据源: {data.get('data_source', '未知')}")
        print(f"  热点板块数量: {len(data.get('hot_sectors', []))}")
        print(f"  北向资金: {data.get('capital_flow', {}).get('northbound_in', 'N/A')}亿")
        print(f"  主力资金: {data.get('capital_flow', {}).get('main_net_in', 'N/A')}亿")
        
        return True
    except Exception as e:
        print(f"✗ 东方财富数据源测试失败: {e}")
        return False

def test_data_source_switching():
    """测试数据源切换机制"""
    print("\n=== 测试数据源切换机制 ===")
    
    try:
        # 创建数据采集Agent，使用不存在的数据源，触发自动切换
        agent = DataCollectorAgent(primary_source='invalid')
        
        # 测试数据采集
        data = agent.collect_market_data()
        
        print(f"✓ 数据源切换测试成功")
        print(f"  最终使用的数据源: {data.get('data_source', '未知')}")
        print(f"  热点板块数量: {len(data.get('hot_sectors', []))}")
        
        return True
    except Exception as e:
        print(f"✗ 数据源切换测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试多数据源功能...")
    
    # 测试各个数据源
    akshare_success = test_akshare_data_source()
    sina_success = test_sina_data_source()
    eastmoney_success = test_eastmoney_data_source()
    switching_success = test_data_source_switching()
    
    # 汇总测试结果
    print("\n=== 测试结果汇总 ===")
    print(f"AKShare数据源: {'✓ 成功' if akshare_success else '✗ 失败'}")
    print(f"新浪财经数据源: {'✓ 成功' if sina_success else '✗ 失败'}")
    print(f"东方财富数据源: {'✓ 成功' if eastmoney_success else '✗ 失败'}")
    print(f"数据源切换机制: {'✓ 成功' if switching_success else '✗ 失败'}")
    
    # 计算总体结果
    total_tests = 4
    passed_tests = sum([akshare_success, sina_success, eastmoney_success, switching_success])
    
    print(f"\n总体测试结果: {passed_tests}/{total_tests} 个测试通过")
    
    if passed_tests == total_tests:
        print("🎉 所有数据源测试都通过了！")
        return 0
    else:
        print("⚠️  部分数据源测试失败，需要检查配置和网络连接")
        return 1

if __name__ == "__main__":
    sys.exit(main())
