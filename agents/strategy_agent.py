#!/usr/bin/env python3
"""
策略优化Agent
负责基于历史数据优化交易策略
"""

import time
import json
import random
from datetime import datetime, timedelta
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dingtalk_sender import DingTalkSender

class StrategyOptimizerAgent:
    def __init__(self):
        self.sender = DingTalkSender()
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(project_root, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.strategies = {
            "technical_analysis": {
                "name": "技术分析策略",
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
            },
            "trend_following": {
                "name": "趋势跟踪策略",
                "parameters": {
                    "ma_period": 20,
                    "trend_threshold": 0.03,
                    "stop_loss": 0.05
                },
                "performance": {
                    "win_rate": 0.55,
                    "average_return": 0.03,
                    "max_drawdown": 0.1
                }
            },
            "mean_reversion": {
                "name": "均值回归策略",
                "parameters": {
                    "mean_period": 30,
                    "deviation_threshold": 0.05,
                    "holding_period": 5
                },
                "performance": {
                    "win_rate": 0.58,
                    "average_return": 0.015,
                    "max_drawdown": 0.06
                }
            }
        }

    def optimize_strategy(self, strategy_name, data):
        """优化策略"""
        try:
            if strategy_name not in self.strategies:
                return {"error": "策略不存在"}

            strategy = self.strategies[strategy_name]
            original_params = strategy['parameters'].copy()

            # 模拟优化过程
            if strategy_name == "technical_analysis":
                # 优化权重参数
                new_params = {}
                for param, value in strategy['parameters'].items():
                    # 随机调整参数
                    adjustment = random.uniform(-0.1, 0.1)
                    new_value = max(0, min(1, value + adjustment))
                    new_params[param] = new_value
                
                # 归一化权重
                total = sum(new_params.values())
                for param in new_params:
                    new_params[param] = new_params[param] / total
            
            elif strategy_name == "trend_following":
                # 优化趋势跟踪参数
                new_params = {
                    "ma_period": int(max(5, min(50, strategy['parameters']['ma_period'] + random.randint(-5, 5)))),
                    "trend_threshold": max(0.01, min(0.05, strategy['parameters']['trend_threshold'] + random.uniform(-0.01, 0.01))),
                    "stop_loss": max(0.03, min(0.1, strategy['parameters']['stop_loss'] + random.uniform(-0.01, 0.01)))
                }
            
            elif strategy_name == "mean_reversion":
                # 优化均值回归参数
                new_params = {
                    "mean_period": int(max(10, min(60, strategy['parameters']['mean_period'] + random.randint(-10, 10)))),
                    "deviation_threshold": max(0.02, min(0.1, strategy['parameters']['deviation_threshold'] + random.uniform(-0.01, 0.01))),
                    "holding_period": int(max(1, min(10, strategy['parameters']['holding_period'] + random.randint(-2, 2))))
                }

            # 模拟性能评估
            new_performance = {
                "win_rate": max(0.4, min(0.8, strategy['performance']['win_rate'] + random.uniform(-0.05, 0.05))),
                "average_return": max(0.005, min(0.05, strategy['performance']['average_return'] + random.uniform(-0.005, 0.005))),
                "max_drawdown": max(0.03, min(0.15, strategy['performance']['max_drawdown'] + random.uniform(-0.01, 0.01)))
            }

            # 更新策略参数
            self.strategies[strategy_name]['parameters'] = new_params
            self.strategies[strategy_name]['performance'] = new_performance

            return {
                "strategy_name": strategy_name,
                "original_parameters": original_params,
                "optimized_parameters": new_params,
                "performance": new_performance,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"[StrategyAgent] 优化策略失败: {e}")
            return {"error": str(e)}

    def evaluate_strategy(self, strategy_name, data):
        """评估策略性能"""
        try:
            if strategy_name not in self.strategies:
                return {"error": "策略不存在"}

            strategy = self.strategies[strategy_name]

            # 模拟评估过程
            evaluation = {
                "strategy_name": strategy_name,
                "strategy": strategy['name'],
                "parameters": strategy['parameters'],
                "performance": strategy['performance'],
                "backtest_results": {
                    "total_trades": random.randint(50, 200),
                    "winning_trades": int(strategy['performance']['win_rate'] * random.randint(50, 200)),
                    "losing_trades": random.randint(20, 100),
                    "total_return": round(random.uniform(0.1, 0.5), 2),
                    "sharpe_ratio": round(random.uniform(0.5, 2.0), 2),
                    "max_drawdown": strategy['performance']['max_drawdown'],
                    "average_holding_period": random.randint(1, 10)
                },
                "timestamp": datetime.now().isoformat()
            }

            return evaluation
        except Exception as e:
            print(f"[StrategyAgent] 评估策略失败: {e}")
            return {"error": str(e)}

    def generate_strategy_suggestions(self):
        """生成策略建议"""
        try:
            # 评估所有策略
            evaluations = []
            for strategy_name in self.strategies:
                evaluation = self.evaluate_strategy(strategy_name, {})
                if "error" not in evaluation:
                    evaluations.append(evaluation)

            # 按夏普比率排序
            evaluations.sort(key=lambda x: x['backtest_results']['sharpe_ratio'], reverse=True)

            # 生成建议
            suggestions = {
                "timestamp": datetime.now().isoformat(),
                "top_strategies": evaluations[:2],
                "market_conditions": self._analyze_market_conditions(),
                "recommendations": []
            }

            # 根据市场情况生成具体建议
            if suggestions['market_conditions']['trend'] == "上升":
                suggestions['recommendations'].append({
                    "strategy": "trend_following",
                    "reason": "市场处于上升趋势，适合趋势跟踪策略",
                    "parameters": {
                        "ma_period": 20,
                        "trend_threshold": 0.03,
                        "stop_loss": 0.05
                    }
                })
            elif suggestions['market_conditions']['volatility'] == "高":
                suggestions['recommendations'].append({
                    "strategy": "mean_reversion",
                    "reason": "市场波动较大，适合均值回归策略",
                    "parameters": {
                        "mean_period": 30,
                        "deviation_threshold": 0.05,
                        "holding_period": 5
                    }
                })
            else:
                suggestions['recommendations'].append({
                    "strategy": "technical_analysis",
                    "reason": "市场处于震荡期，适合技术分析策略",
                    "parameters": {
                        "macd_weight": 0.3,
                        "kdj_weight": 0.25,
                        "rsi_weight": 0.2,
                        "volume_weight": 0.15,
                        "ma_weight": 0.1
                    }
                })

            # 发送策略建议通知
            self._send_strategy_suggestion(suggestions)

            # 保存策略建议
            suggestion_file = os.path.join(self.data_dir, f"strategy_suggestion_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
            with open(suggestion_file, 'w', encoding='utf-8') as f:
                json.dump(suggestions, f, indent=2, ensure_ascii=False)

            return suggestions
        except Exception as e:
            print(f"[StrategyAgent] 生成策略建议失败: {e}")
            return {"error": str(e)}

    def tune_parameters(self, strategy_name):
        """调优策略参数"""
        try:
            if strategy_name not in self.strategies:
                return {"error": "策略不存在"}

            # 多次优化寻找最优参数
            best_result = None
            best_performance = 0

            for _ in range(10):
                result = self.optimize_strategy(strategy_name, {})
                if "error" not in result:
                    # 计算综合性能得分
                    performance_score = (
                        result['performance']['win_rate'] * 0.4 +
                        result['performance']['average_return'] * 20 +
                        (1 - result['performance']['max_drawdown']) * 0.3
                    )
                    if performance_score > best_performance:
                        best_performance = performance_score
                        best_result = result

            return best_result
        except Exception as e:
            print(f"[StrategyAgent] 调优策略参数失败: {e}")
            return {"error": str(e)}

    def backtest_strategy(self, strategy_name, data):
        """回测策略"""
        try:
            if strategy_name not in self.strategies:
                return {"error": "策略不存在"}

            # 模拟回测过程
            backtest_result = {
                "strategy_name": strategy_name,
                "strategy": self.strategies[strategy_name]['name'],
                "parameters": self.strategies[strategy_name]['parameters'],
                "start_date": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "results": {
                    "total_trades": random.randint(100, 300),
                    "winning_trades": random.randint(60, 180),
                    "losing_trades": random.randint(40, 120),
                    "win_rate": round(random.uniform(0.5, 0.7), 2),
                    "total_return": round(random.uniform(0.1, 0.6), 2),
                    "average_return_per_trade": round(random.uniform(0.01, 0.03), 3),
                    "max_drawdown": round(random.uniform(0.05, 0.15), 2),
                    "sharpe_ratio": round(random.uniform(0.8, 2.5), 2),
                    "average_holding_period": random.randint(1, 7),
                    "profit_factor": round(random.uniform(1.2, 2.0), 2)
                },
                "timestamp": datetime.now().isoformat()
            }

            # 发送回测结果通知
            self._send_backtest_result(backtest_result)

            # 保存回测结果
            backtest_file = os.path.join(self.data_dir, f"backtest_{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
            with open(backtest_file, 'w', encoding='utf-8') as f:
                json.dump(backtest_result, f, indent=2, ensure_ascii=False)

            return backtest_result
        except Exception as e:
            print(f"[StrategyAgent] 回测策略失败: {e}")
            return {"error": str(e)}

    def _analyze_market_conditions(self):
        """分析市场情况"""
        # 模拟市场分析
        return {
            "trend": random.choice(["上升", "下降", "震荡"]),
            "volatility": random.choice(["高", "中", "低"]),
            "market_sentiment": random.choice(["乐观", "中性", "悲观"]),
            "sector_rotation": random.choice(["科技", "金融", "消费", "医药"])
        }

    def _send_strategy_suggestion(self, suggestions):
        """发送策略建议通知"""
        try:
            content = f"""
📊 策略优化建议

⏰ 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 市场情况
📈 趋势: {suggestions['market_conditions']['trend']}
📊 波动率: {suggestions['market_conditions']['volatility']}
😃 市场情绪: {suggestions['market_conditions']['market_sentiment']}
🔄 板块轮动: {suggestions['market_conditions']['sector_rotation']}

## 推荐策略
"""

            for i, rec in enumerate(suggestions['recommendations'], 1):
                content += f"### {i}. {self.strategies[rec['strategy']]['name']}\n"
                content += f"📋 推荐理由: {rec['reason']}\n"
                content += "🔧 参数建议: "
                for param, value in rec['parameters'].items():
                    content += f"{param}={value}, "
                content = content.rstrip(', ') + "\n\n"

            # 添加策略性能
            content += "## 策略性能排名\n"
            for i, strategy in enumerate(suggestions['top_strategies'], 1):
                content += f"{i}. {strategy['strategy']}: "
                content += f"胜率={strategy['performance']['win_rate']:.2f}, "
                content += f"平均收益={strategy['performance']['average_return']:.2f}, "
                content += f"最大回撤={strategy['performance']['max_drawdown']:.2f}\n"

            self.sender.send_message(
                title="📊 策略优化建议",
                content=content,
                msg_type="markdown",
                level="info"
            )
        except Exception as e:
            print(f"[StrategyAgent] 发送策略建议失败: {e}")

    def _send_backtest_result(self, backtest_result):
        """发送回测结果通知"""
        try:
            content = f"""
📊 策略回测结果

⏰ 回测时间: {backtest_result['timestamp']}
📈 策略: {backtest_result['strategy']}
📅 回测周期: {backtest_result['start_date']} 至 {backtest_result['end_date']}

## 回测结果
📊 总交易次数: {backtest_result['results']['total_trades']}
✅ 盈利交易: {backtest_result['results']['winning_trades']}
❌ 亏损交易: {backtest_result['results']['losing_trades']}
📈 胜率: {backtest_result['results']['win_rate']:.2f}
💰 总收益: {backtest_result['results']['total_return']:.2f}%
📊 平均每笔收益: {backtest_result['results']['average_return_per_trade']:.2f}%
📉 最大回撤: {backtest_result['results']['max_drawdown']:.2f}%
📊 夏普比率: {backtest_result['results']['sharpe_ratio']:.2f}
⏰ 平均持仓周期: {backtest_result['results']['average_holding_period']}天
📊 盈利因子: {backtest_result['results']['profit_factor']:.2f}

## 参数配置
"""

            for param, value in backtest_result['parameters'].items():
                content += f"- {param}: {value}\n"

            self.sender.send_message(
                title="📊 策略回测结果",
                content=content,
                msg_type="markdown",
                level="info"
            )
        except Exception as e:
            print(f"[StrategyAgent] 发送回测结果失败: {e}")

    def run(self, interval=3600):  # 默认1小时
        """运行Agent"""
        print(f"策略优化Agent启动，间隔: {interval}秒")

        while True:
            try:
                current_hour = datetime.now().hour

                # 每天收盘后运行策略优化
                if current_hour == 15:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 运行策略优化...")
                    
                    # 优化所有策略
                    for strategy_name in self.strategies:
                        self.optimize_strategy(strategy_name, {})
                    
                    # 生成策略建议
                    self.generate_strategy_suggestions()

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n策略优化Agent停止")
                break
            except Exception as e:
                print(f"策略优化错误: {e}")
                time.sleep(60)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='策略优化Agent')
    parser.add_argument('--test', action='store_true', help='测试模式：运行一次策略优化并打印结果')
    parser.add_argument('--interval', type=int, default=3600, help='检查间隔（秒），默认3600秒（1小时）')
    args = parser.parse_args()

    agent = StrategyOptimizerAgent()

    if args.test:
        print("=== 策略优化Agent测试模式 ===")
        
        # 测试策略优化
        print("\n1. 测试策略优化:")
        result = agent.optimize_strategy("technical_analysis", {})
        print(f"   优化结果: {result}")
        
        # 测试策略评估
        print("\n2. 测试策略评估:")
        evaluation = agent.evaluate_strategy("technical_analysis", {})
        print(f"   评估结果: {evaluation}")
        
        # 测试生成策略建议
        print("\n3. 测试生成策略建议:")
        suggestions = agent.generate_strategy_suggestions()
        print(f"   策略建议: {suggestions}")
        
        # 测试参数调优
        print("\n4. 测试参数调优:")
        tuning = agent.tune_parameters("technical_analysis")
        print(f"   调优结果: {tuning}")
        
        # 测试回测策略
        print("\n5. 测试回测策略:")
        backtest = agent.backtest_strategy("technical_analysis", {})
        print(f"   回测结果: {backtest}")
        
        print("\n测试完成，退出。")
    else:
        print(f"策略优化Agent启动，间隔: {args.interval}秒")
        agent.run(interval=args.interval)