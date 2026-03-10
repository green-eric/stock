#!/usr/bin/env python3
"""
数据存储测试用例
测试Redis和PostgreSQL的集成功能
"""

import unittest
import sys
import os
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.storage import DataStorage

class TestDataStorage(unittest.TestCase):
    """测试数据存储模块"""
    
    def setUp(self):
        self.storage = DataStorage()
    
    def test_save_market_data(self):
        """测试保存市场数据"""
        test_data = {
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
        result = self.storage.save_market_data(test_data)
        self.assertTrue(result)
    
    def test_get_market_data(self):
        """测试获取市场数据"""
        # 先保存数据
        test_data = {
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
        self.storage.save_market_data(test_data)
        
        # 再获取数据
        data = self.storage.get_market_data("002594")
        self.assertIsInstance(data, dict)
        self.assertEqual(data['symbol'], "002594")
        self.assertEqual(data['name'], "比亚迪")
    
    def test_save_technical_analysis(self):
        """测试保存技术分析结果"""
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "symbol": "002594",
            "name": "比亚迪",
            "indicators": {
                "macd": "金叉",
                "kdj": "中性",
                "rsi": 62.5,
                "volume_ratio": 1.2,
                "ma5": 222.0,
                "ma10": 218.0,
                "ma20": 215.0
            },
            "score": 8.2,
            "signal": "买入",
            "suggestions": {
                "entry_price": "220-225",
                "stop_loss": 200.0,
                "target_price": 240.0
            }
        }
        result = self.storage.save_technical_analysis(test_data)
        self.assertTrue(result)
    
    def test_get_technical_analysis(self):
        """测试获取技术分析结果"""
        # 先保存数据
        test_data = {
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
            "signal": "买入"
        }
        self.storage.save_technical_analysis(test_data)
        
        # 再获取数据
        analysis = self.storage.get_technical_analysis("002594")
        self.assertIsInstance(analysis, list)
        self.assertGreater(len(analysis), 0)
        self.assertEqual(analysis[0]['symbol'], "002594")
    
    def test_save_trade(self):
        """测试保存交易记录"""
        test_data = {
            "trade_id": "TRADE1234567890AB",
            "order_id": "ORD1234567890AB",
            "symbol": "002594",
            "name": "比亚迪",
            "side": "buy",
            "price": 225.0,
            "quantity": 100,
            "amount": 22500,
            "timestamp": datetime.now().isoformat(),
            "strategy": "technical_analysis",
            "signal_id": "SIG12345678"
        }
        result = self.storage.save_trade(test_data)
        self.assertTrue(result)
    
    def test_get_trades(self):
        """测试获取交易记录"""
        # 先保存数据
        test_data = {
            "trade_id": "TRADE1234567890AB",
            "order_id": "ORD1234567890AB",
            "symbol": "002594",
            "name": "比亚迪",
            "side": "buy",
            "price": 225.0,
            "quantity": 100,
            "amount": 22500,
            "timestamp": datetime.now().isoformat(),
            "strategy": "technical_analysis",
            "signal_id": "SIG12345678"
        }
        self.storage.save_trade(test_data)
        
        # 再获取数据
        trades = self.storage.get_trades("002594")
        self.assertIsInstance(trades, list)
        self.assertGreater(len(trades), 0)
        self.assertEqual(trades[0]['symbol'], "002594")
    
    def test_save_risk_assessment(self):
        """测试保存风险评估结果"""
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "market_risk": {
                "total_risk": 0.3,
                "risk_level": "低"
            },
            "position_risk": {
                "total_risk": 0.2,
                "overall_risk_level": "低"
            }
        }
        result = self.storage.save_risk_assessment(test_data)
        self.assertTrue(result)
    
    def test_get_risk_assessments(self):
        """测试获取风险评估记录"""
        # 先保存数据
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "market_risk": {
                "total_risk": 0.3,
                "risk_level": "低"
            },
            "position_risk": {
                "total_risk": 0.2,
                "overall_risk_level": "低"
            }
        }
        self.storage.save_risk_assessment(test_data)
        
        # 再获取数据
        assessments = self.storage.get_risk_assessments()
        self.assertIsInstance(assessments, list)
        self.assertGreater(len(assessments), 0)
    
    def test_save_strategy_optimization(self):
        """测试保存策略优化结果"""
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "strategy_name": "technical_analysis",
            "parameters": {
                "macd_weight": 0.3,
                "kdj_weight": 0.25,
                "rsi_weight": 0.2,
                "volume_weight": 0.15,
                "ma_weight": 0.1
            },
            "performance": {
                "win_rate": 0.6,
                "average_return": 0.02,
                "max_drawdown": 0.08
            }
        }
        result = self.storage.save_strategy_optimization(test_data)
        self.assertTrue(result)
    
    def test_get_strategy_optimizations(self):
        """测试获取策略优化记录"""
        # 先保存数据
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "strategy_name": "technical_analysis",
            "parameters": {
                "macd_weight": 0.3,
                "kdj_weight": 0.25
            },
            "performance": {
                "win_rate": 0.6,
                "average_return": 0.02
            }
        }
        self.storage.save_strategy_optimization(test_data)
        
        # 再获取数据
        optimizations = self.storage.get_strategy_optimizations("technical_analysis")
        self.assertIsInstance(optimizations, list)
        self.assertGreater(len(optimizations), 0)
        self.assertEqual(optimizations[0]['strategy_name'], "technical_analysis")
    
    def tearDown(self):
        """清理资源"""
        self.storage.close()

if __name__ == '__main__':
    unittest.main()