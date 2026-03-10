#!/usr/bin/env python3
"""
Agent测试用例
测试各个Agent的核心功能
"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_agent import DataCollectorAgent
from agents.technical_agent import TechnicalAnalysisAgent
from agents.risk_agent import RiskControllerAgent
from agents.trade_agent import TradeExecutorAgent
from agents.strategy_agent import StrategyOptimizerAgent

class TestDataAgent(unittest.TestCase):
    """测试数据采集Agent"""
    
    def setUp(self):
        self.agent = DataCollectorAgent(use_real_data=False)
    
    def test_collect_market_data(self):
        """测试收集市场数据"""
        data = self.agent.collect_market_data()
        self.assertIsInstance(data, dict)
        self.assertIn('timestamp', data)
        self.assertIn('hot_sectors', data)
        self.assertIn('capital_flow', data)
        self.assertIsInstance(data['hot_sectors'], list)
        self.assertIsInstance(data['capital_flow'], dict)
    
    def test_send_market_summary(self):
        """测试发送市场总结"""
        result = self.agent.send_market_summary()
        self.assertIsInstance(result, bool)

class TestTechnicalAgent(unittest.TestCase):
    """测试技术分析Agent"""
    
    def setUp(self):
        self.agent = TechnicalAnalysisAgent()
    
    def test_analyze_stock(self):
        """测试分析股票"""
        test_stock = {"code": "002594", "name": "比亚迪", "price": 225.0}
        result = self.agent.analyze_stock(test_stock)
        self.assertIsInstance(result, dict)
        self.assertIn('code', result)
        self.assertIn('name', result)
        self.assertIn('price', result)
        self.assertIn('indicators', result)
        self.assertIn('score', result)
        self.assertIn('signal', result)
    
    def test_send_analysis_results(self):
        """测试发送分析结果"""
        result = self.agent.send_analysis_results()
        self.assertIsInstance(result, int)

class TestRiskAgent(unittest.TestCase):
    """测试风险控制Agent"""
    
    def setUp(self):
        self.agent = RiskControllerAgent()
    
    def test_assess_market_risk(self):
        """测试评估市场风险"""
        market_data = {
            'hot_sectors': [{'change': 2.5}, {'change': -1.2}, {'change': 3.1}],
            'capital_flow': {'northbound_in': 1.2, 'main_net_in': 3.5, 'retail_net_in': -0.8}
        }
        result = self.agent.assess_market_risk(market_data)
        self.assertIsInstance(result, dict)
        self.assertIn('total_risk', result)
        self.assertIn('risk_level', result)
    
    def test_assess_position_risk(self):
        """测试评估持仓风险"""
        positions = {
            "002594": {
                "symbol": "002594",
                "name": "比亚迪",
                "current_price": 210.0,
                "entry_price": 225.0,
                "quantity": 100
            }
        }
        result = self.agent.assess_position_risk(positions)
        self.assertIsInstance(result, dict)
        self.assertIn('total_risk', result)
        self.assertIn('overall_risk_level', result)
    
    def test_execute_stop_loss(self):
        """测试执行止损操作"""
        position = {
            "symbol": "002594",
            "name": "比亚迪",
            "current_price": 200.0,
            "entry_price": 225.0,
            "quantity": 100
        }
        result = self.agent.execute_stop_loss(position)
        self.assertIsInstance(result, dict)
        self.assertIn('symbol', result)
        self.assertIn('side', result)
        self.assertEqual(result['side'], 'sell')
    
    def test_generate_risk_report(self):
        """测试生成风险报告"""
        result = self.agent.generate_risk_report()
        self.assertIsInstance(result, bool)

class TestTradeAgent(unittest.TestCase):
    """测试交易执行Agent"""
    
    def setUp(self):
        self.agent = TradeExecutorAgent(use_simulated=True)
    
    def test_place_order(self):
        """测试下单"""
        order = {
            "symbol": "002594",
            "name": "比亚迪",
            "side": "buy",
            "price": 225.0,
            "quantity": 100
        }
        result = self.agent.place_order(order)
        self.assertIsInstance(result, dict)
        self.assertIn('order_id', result)
        self.assertIn('status', result)
    
    def test_cancel_order(self):
        """测试撤单"""
        # 先下单
        order = {
            "symbol": "002594",
            "name": "比亚迪",
            "side": "buy",
            "price": 225.0,
            "quantity": 100
        }
        place_result = self.agent.place_order(order)
        order_id = place_result['order_id']
        
        # 再撤单
        cancel_result = self.agent.cancel_order(order_id)
        self.assertIsInstance(cancel_result, dict)
        self.assertIn('status', cancel_result)
        self.assertEqual(cancel_result['status'], 'cancelled')
    
    def test_get_order_status(self):
        """测试获取订单状态"""
        # 先下单
        order = {
            "symbol": "002594",
            "name": "比亚迪",
            "side": "buy",
            "price": 225.0,
            "quantity": 100
        }
        place_result = self.agent.place_order(order)
        order_id = place_result['order_id']
        
        # 获取订单状态
        status_result = self.agent.get_order_status(order_id)
        self.assertIsInstance(status_result, dict)
        self.assertIn('order_id', status_result)
        self.assertIn('status', status_result)
    
    def test_get_positions(self):
        """测试获取持仓"""
        result = self.agent.get_positions()
        self.assertIsInstance(result, dict)
        self.assertIn('balance', result)
        self.assertIn('positions', result)
        self.assertIn('total_value', result)

class TestStrategyAgent(unittest.TestCase):
    """测试策略优化Agent"""
    
    def setUp(self):
        self.agent = StrategyOptimizerAgent()
    
    def test_optimize_strategy(self):
        """测试优化策略"""
        result = self.agent.optimize_strategy("technical_analysis", {})
        self.assertIsInstance(result, dict)
        self.assertIn('strategy_name', result)
        self.assertIn('optimized_parameters', result)
        self.assertIn('performance', result)
    
    def test_evaluate_strategy(self):
        """测试评估策略性能"""
        result = self.agent.evaluate_strategy("technical_analysis", {})
        self.assertIsInstance(result, dict)
        self.assertIn('strategy_name', result)
        self.assertIn('performance', result)
        self.assertIn('backtest_results', result)
    
    def test_generate_strategy_suggestions(self):
        """测试生成策略建议"""
        result = self.agent.generate_strategy_suggestions()
        self.assertIsInstance(result, dict)
        self.assertIn('timestamp', result)
        self.assertIn('top_strategies', result)
        self.assertIn('recommendations', result)
    
    def test_backtest_strategy(self):
        """测试回测策略"""
        result = self.agent.backtest_strategy("technical_analysis", {})
        self.assertIsInstance(result, dict)
        self.assertIn('strategy_name', result)
        self.assertIn('results', result)
        self.assertIn('win_rate', result['results'])
        self.assertIn('total_return', result['results'])

if __name__ == '__main__':
    unittest.main()