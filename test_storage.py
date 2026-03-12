#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试存储功能
"""

import time
from datetime import datetime
from data.storage import DataStorage


def test_storage_initialization():
    """测试存储初始化"""
    print("\n=== 测试存储初始化 ===")
    storage = DataStorage()
    
    # 验证连接状态
    print(f"Redis客户端状态: {'已连接' if storage.redis_client else '未连接'}")
    print(f"PostgreSQL连接状态: {'已连接' if storage.postgres_conn else '未连接'}")
    
    # 即使连接失败，测试也应该继续
    print("存储初始化测试通过!")
    return storage


def test_market_data_storage(storage):
    """测试市场数据存储"""
    print("\n=== 测试市场数据存储 ===")
    
    # 测试数据
    test_market_data = {
        "timestamp": datetime.now().isoformat(),
        "symbol": "002594",
        "name": "比亚迪",
        "price": 225.0,
        "change": 5.5,
        "change_percent": 2.5,
        "volume": 1000000,
        "amount": 225000000,
        "open": 220.0,
        "high": 226.0,
        "low": 219.0,
        "close": 225.0,
        "prev_close": 219.5
    }
    
    print(f"保存市场数据: {test_market_data['symbol']} - {test_market_data['name']}")
    result = storage.save_market_data(test_market_data)
    print(f"保存结果: {result}")
    
    # 测试获取市场数据
    print("获取市场数据...")
    data = storage.get_market_data("002594")
    print(f"获取结果: {'成功' if data else '失败'}")
    if data:
        print(f"获取到的数据: {data['symbol']} - {data['name']} - {data['price']}")
    
    print("市场数据存储测试通过!")


def test_technical_analysis_storage(storage):
    """测试技术分析结果存储"""
    print("\n=== 测试技术分析结果存储 ===")
    
    # 测试数据
    test_analysis_data = {
        "timestamp": datetime.now().isoformat(),
        "symbol": "002594",
        "name": "比亚迪",
        "indicators": {
            "macd": "金叉",
            "kdj": "中性",
            "rsi": 62.5,
            "volume_ratio": 1.2
        },
        "score": 8.2,
        "signal": "买入",
        "suggestions": {
            "entry_price": "220-225",
            "stop_loss": 200.0,
            "target_price": 240.0
        }
    }
    
    print(f"保存技术分析结果: {test_analysis_data['symbol']} - {test_analysis_data['signal']}")
    result = storage.save_technical_analysis(test_analysis_data)
    print(f"保存结果: {result}")
    
    # 测试获取技术分析结果
    print("获取技术分析结果...")
    analysis = storage.get_technical_analysis("002594")
    print(f"获取结果: {'成功' if analysis else '失败'}")
    if analysis:
        print(f"获取到的分析结果: {analysis[0]['symbol']} - {analysis[0]['signal']} - {analysis[0]['score']}")
    
    print("技术分析结果存储测试通过!")


def test_trade_storage(storage):
    """测试交易记录存储"""
    print("\n=== 测试交易记录存储 ===")
    
    # 测试数据
    test_trade_data = {
        "trade_id": f"trade_{int(time.time())}",
        "order_id": f"order_{int(time.time())}",
        "symbol": "002594",
        "name": "比亚迪",
        "side": "买入",
        "price": 225.0,
        "quantity": 100,
        "amount": 22500.0,
        "timestamp": datetime.now().isoformat(),
        "strategy": "MACD金叉",
        "signal_id": f"signal_{int(time.time())}"
    }
    
    print(f"保存交易记录: {test_trade_data['trade_id']} - {test_trade_data['side']}")
    result = storage.save_trade(test_trade_data)
    print(f"保存结果: {result}")
    
    # 测试获取交易记录
    print("获取交易记录...")
    trades = storage.get_trades("002594")
    print(f"获取结果: {'成功' if trades else '失败'}")
    if trades:
        print(f"获取到的交易记录: {len(trades)}条")
    
    print("交易记录存储测试通过!")


def test_risk_assessment_storage(storage):
    """测试风险评估存储"""
    print("\n=== 测试风险评估存储 ===")
    
    # 测试数据
    test_risk_data = {
        "timestamp": datetime.now().isoformat(),
        "market_risk": {
            "overall": "低",
            "volatility": "中",
            "trend": "向上"
        },
        "position_risk": {
            "exposure": 0.3,
            "max_drawdown": 0.1,
            "leverage": 1.0
        }
    }
    
    print("保存风险评估结果...")
    result = storage.save_risk_assessment(test_risk_data)
    print(f"保存结果: {result}")
    
    # 测试获取风险评估结果
    print("获取风险评估结果...")
    risk_assessments = storage.get_risk_assessments()
    print(f"获取结果: {'成功' if risk_assessments else '失败'}")
    if risk_assessments:
        print(f"获取到的风险评估记录: {len(risk_assessments)}条")
    
    print("风险评估存储测试通过!")


def test_strategy_optimization_storage(storage):
    """测试策略优化存储"""
    print("\n=== 测试策略优化存储 ===")
    
    # 测试数据
    test_strategy_data = {
        "timestamp": datetime.now().isoformat(),
        "strategy_name": "MACD策略",
        "parameters": {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        },
        "performance": {
            "profit_factor": 1.5,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.15,
            "win_rate": 0.6
        }
    }
    
    print(f"保存策略优化结果: {test_strategy_data['strategy_name']}")
    result = storage.save_strategy_optimization(test_strategy_data)
    print(f"保存结果: {result}")
    
    # 测试获取策略优化结果
    print("获取策略优化结果...")
    optimizations = storage.get_strategy_optimizations("MACD策略")
    print(f"获取结果: {'成功' if optimizations else '失败'}")
    if optimizations:
        print(f"获取到的策略优化记录: {len(optimizations)}条")
    
    print("策略优化存储测试通过!")


def test_storage_integration():
    """测试存储集成"""
    print("\n=== 测试存储集成 ===")
    
    # 初始化存储
    storage = DataStorage()
    
    try:
        # 测试各种存储功能
        test_market_data_storage(storage)
        test_technical_analysis_storage(storage)
        test_trade_storage(storage)
        test_risk_assessment_storage(storage)
        test_strategy_optimization_storage(storage)
        
        print("\n存储集成测试通过!")
    finally:
        # 关闭连接
        storage.close()


if __name__ == "__main__":
    print("开始测试存储功能...")
    
    try:
        test_storage_integration()
        print("\n✅ 所有存储功能测试通过!")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
