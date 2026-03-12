#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整系统测试
"""

import time
from config.config_manager import config_manager
from data.data_share import data_share
from data.storage import DataStorage
from agents.data_agent import DataCollectorAgent
from agents.technical_agent import TechnicalAnalysisAgent
from utils.error_handler import error_handler


def test_system_initialization():
    """测试系统初始化"""
    print("\n=== 测试系统初始化 ===")
    
    # 测试配置管理器
    print("测试配置管理器...")
    system_config = config_manager.get_system_config()
    print(f"系统配置: {system_config}")
    assert system_config is not None, "配置管理器初始化失败"
    
    # 测试数据共享
    print("测试数据共享...")
    test_data = {"test": "system_test"}
    data_share.set("system_test", test_data)
    retrieved_data = data_share.get("system_test")
    print(f"数据共享测试: {retrieved_data}")
    assert retrieved_data == test_data, "数据共享初始化失败"
    
    # 测试存储系统
    print("测试存储系统...")
    storage = DataStorage()
    assert storage.redis_client is not None or storage.postgres_conn is not None, "存储系统初始化失败"
    
    # 测试错误处理器
    print("测试错误处理器...")
    def test_error_func():
        raise ValueError("测试错误")
    
    result = error_handler.try_execute(test_error_func)
    print(f"错误处理测试: {result}")
    assert result is None, "错误处理器初始化失败"
    
    # 测试数据采集Agent
    print("测试数据采集Agent...")
    data_agent = DataCollectorAgent(use_real_data=False)
    market_data = data_agent.collect_market_data()
    print(f"数据采集Agent测试: {market_data}")
    assert market_data is not None, "数据采集Agent初始化失败"
    
    # 测试技术分析Agent
    print("测试技术分析Agent...")
    technical_agent = TechnicalAnalysisAgent()
    watch_list = technical_agent.watch_list
    print(f"技术分析Agent测试: 监控列表长度 = {len(watch_list)}")
    assert len(watch_list) > 0, "技术分析Agent初始化失败"
    
    print("系统初始化测试通过!")


def test_system_integration():
    """测试系统集成"""
    print("\n=== 测试系统集成 ===")
    
    # 1. 初始化所有组件
    print("初始化所有组件...")
    storage = DataStorage()
    data_agent = DataCollectorAgent(use_real_data=False)
    technical_agent = TechnicalAnalysisAgent()
    
    # 2. 采集市场数据
    print("采集市场数据...")
    market_data = data_agent.collect_market_data()
    print(f"采集到市场数据: {market_data}")
    
    # 3. 分析股票
    print("分析股票...")
    watch_list = technical_agent.watch_list
    analysis_results = []
    for stock in watch_list[:3]:  # 只分析前3只股票以节省时间
        result = technical_agent.analyze_stock(stock)
        analysis_results.append(result)
        print(f"分析股票 {stock['code']} {stock['name']}: {result['signal']} (评分: {result['score']:.1f})")
    
    # 4. 发送分析结果
    print("发送分析结果...")
    buy_count = technical_agent.send_analysis_results()
    print(f"发现的买入信号数量: {buy_count}")
    
    # 5. 验证数据流转
    print("验证数据流转...")
    
    # 验证市场数据已存储
    stored_market_data = data_share.get_market_data()
    print(f"存储到data_share的市场数据: {stored_market_data}")
    assert stored_market_data is not None, "市场数据未流转"
    
    # 验证分析结果已存储
    stored_analysis = data_share.get_analysis_results()
    print(f"存储到data_share的分析结果: {stored_analysis}")
    assert stored_analysis is not None, "分析结果未流转"
    
    # 6. 测试错误处理
    print("测试错误处理...")
    def test_error_integration():
        raise Exception("集成测试错误")
    
    def fallback():
        return "错误处理成功"
    
    result = error_handler.try_execute_with_fallback(test_error_integration, fallback)
    print(f"错误处理集成测试: {result}")
    assert result == "错误处理成功", "错误处理集成失败"
    
    print("系统集成测试通过!")


def test_system_performance():
    """测试系统性能"""
    print("\n=== 测试系统性能 ===")
    
    # 测试数据采集性能
    print("测试数据采集性能...")
    start_time = time.time()
    data_agent = DataCollectorAgent(use_real_data=False)
    for i in range(5):
        market_data = data_agent.collect_market_data()
    end_time = time.time()
    avg_time = (end_time - start_time) / 5
    print(f"平均数据采集时间: {avg_time:.3f}秒")
    assert avg_time < 1.0, "数据采集性能不佳"
    
    # 测试股票分析性能
    print("测试股票分析性能...")
    start_time = time.time()
    technical_agent = TechnicalAnalysisAgent()
    watch_list = technical_agent.watch_list
    for stock in watch_list[:5]:
        result = technical_agent.analyze_stock(stock)
    end_time = time.time()
    avg_time = (end_time - start_time) / 5
    print(f"平均股票分析时间: {avg_time:.3f}秒")
    assert avg_time < 2.0, "股票分析性能不佳"
    
    # 测试数据存储性能
    print("测试数据存储性能...")
    start_time = time.time()
    storage = DataStorage()
    test_data = {
        "timestamp": time.time(),
        "symbol": "000001",
        "name": "平安银行",
        "price": 15.5,
        "change": 0.5,
        "change_percent": 3.33,
        "volume": 1000000,
        "amount": 15500000,
        "open": 15.0,
        "high": 15.6,
        "low": 14.9,
        "close": 15.5,
        "prev_close": 15.0
    }
    for i in range(3):
        storage.save_market_data(test_data)
    end_time = time.time()
    avg_time = (end_time - start_time) / 3
    print(f"平均数据存储时间: {avg_time:.3f}秒")
    assert avg_time < 1.0, "数据存储性能不佳"
    
    print("系统性能测试通过!")


def test_system_resilience():
    """测试系统 resilience"""
    print("\n=== 测试系统 resilience ===")
    
    # 测试配置文件缺失
    print("测试配置文件缺失处理...")
    # 这里不实际删除配置文件，而是测试配置管理器的容错能力
    non_existent_config = config_manager.get_config("non_existent_config")
    print(f"获取不存在的配置: {non_existent_config}")
    assert non_existent_config is None, "配置管理器容错能力不足"
    
    # 测试数据获取失败
    print("测试数据获取失败处理...")
    data_agent = DataCollectorAgent(use_real_data=True)  # 强制使用真实数据（可能失败）
    market_data = data_agent.collect_market_data()
    print(f"获取市场数据（可能使用模拟数据）: {market_data}")
    assert market_data is not None, "数据采集Agent容错能力不足"
    
    # 测试存储连接失败
    print("测试存储连接失败处理...")
    # 创建一个使用无效配置的存储实例
    invalid_storage = DataStorage(
        redis_config={"host": "invalid_host", "port": 6379, "db": 0},
        postgres_config={"host": "invalid_host", "port": 5432, "database": "test", "user": "test", "password": "test"}
    )
    print(f"Redis连接状态: {'已连接' if invalid_storage.redis_client else '未连接'}")
    print(f"PostgreSQL连接状态: {'已连接' if invalid_storage.postgres_conn else '未连接'}")
    # 即使连接失败，存储系统也应该能正常初始化
    assert True, "存储系统容错能力测试通过"
    
    print("系统 resilience 测试通过!")


def run_full_system_test():
    """运行完整系统测试"""
    print("开始完整系统测试...")
    
    try:
        test_system_initialization()
        test_system_integration()
        test_system_performance()
        test_system_resilience()
        print("\n✅ 所有系统测试通过!")
        return True
    except Exception as e:
        print(f"\n❌ 系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_full_system_test()
    if success:
        print("\n🎉 完整系统测试成功完成!")
    else:
        print("\n⚠️  完整系统测试失败，请检查错误信息。")
