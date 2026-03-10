#!/usr/bin/env python3
"""
风险控制Agent
负责监控风险，执行止损操作
"""

import time
import json
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dingtalk import DingTalkSender

class RiskControllerAgent:
    def __init__(self):
        self.sender = DingTalkSender()
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(project_root, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.risk_threshold = 0.05  # 5%风险阈值
        self.max_position = 1000000  # 最大仓位
        self.stop_loss_percent = 0.08  # 8%止损
        self.positions = {}
        self.risk_levels = {}

    def assess_market_risk(self, market_data):
        """评估市场风险"""
        try:
            # 计算市场波动率
            volatility = 0.0
            if market_data and 'hot_sectors' in market_data:
                changes = [sector['change'] for sector in market_data['hot_sectors']]
                if changes:
                    volatility = sum(abs(c) for c in changes) / len(changes)

            # 计算资金流向风险
            capital_risk = 0.0
            if market_data and 'capital_flow' in market_data:
                cf = market_data['capital_flow']
                if cf['northbound_in'] < -1.0:
                    capital_risk += 0.3
                if cf['main_net_in'] < -2.0:
                    capital_risk += 0.4
                if cf['retail_net_in'] > 1.0:
                    capital_risk += 0.2

            # 综合风险评估
            total_risk = volatility * 0.5 + capital_risk * 0.5
            risk_level = "低" if total_risk < 0.3 else "中" if total_risk < 0.6 else "高"

            return {
                "timestamp": datetime.now().isoformat(),
                "volatility": round(volatility, 2),
                "capital_risk": round(capital_risk, 2),
                "total_risk": round(total_risk, 2),
                "risk_level": risk_level
            }
        except Exception as e:
            print(f"[RiskAgent] 评估市场风险失败: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "volatility": 0.0,
                "capital_risk": 0.0,
                "total_risk": 0.5,
                "risk_level": "中"
            }

    def assess_position_risk(self, positions):
        """评估持仓风险"""
        try:
            risk_assessments = {}
            total_risk = 0.0
            total_value = 0.0

            for symbol, position in positions.items():
                # 计算单只股票风险
                current_price = position['current_price']
                entry_price = position['entry_price']
                loss_percent = (current_price - entry_price) / entry_price
                position_value = current_price * position['quantity']
                total_value += position_value

                # 计算风险等级
                if loss_percent < -self.stop_loss_percent:
                    risk_level = "高"
                elif loss_percent < -0.04:
                    risk_level = "中"
                else:
                    risk_level = "低"

                risk_assessments[symbol] = {
                    "symbol": symbol,
                    "name": position['name'],
                    "current_price": current_price,
                    "entry_price": entry_price,
                    "loss_percent": round(loss_percent * 100, 2),
                    "position_value": position_value,
                    "risk_level": risk_level
                }

                # 计算总风险
                total_risk += abs(loss_percent) * (position_value / (total_value or 1))

            overall_risk_level = "低" if total_risk < 0.03 else "中" if total_risk < 0.06 else "高"

            return {
                "timestamp": datetime.now().isoformat(),
                "total_value": total_value,
                "total_risk": round(total_risk, 2),
                "overall_risk_level": overall_risk_level,
                "positions": risk_assessments
            }
        except Exception as e:
            print(f"[RiskAgent] 评估持仓风险失败: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "total_value": 0.0,
                "total_risk": 0.0,
                "overall_risk_level": "低",
                "positions": {}
            }

    def execute_stop_loss(self, position):
        """执行止损操作"""
        try:
            current_price = position['current_price']
            entry_price = position['entry_price']
            loss_percent = (current_price - entry_price) / entry_price

            if loss_percent < -self.stop_loss_percent:
                # 执行止损
                stop_loss_order = {
                    "symbol": position['symbol'],
                    "name": position['name'],
                    "side": "sell",
                    "price": current_price,
                    "quantity": position['quantity'],
                    "amount": current_price * position['quantity'],
                    "reason": "止损",
                    "loss_percent": round(loss_percent * 100, 2),
                    "timestamp": datetime.now().isoformat()
                }

                # 发送止损通知
                content = f"""
🚨 止损操作执行

📊 股票: {position['symbol']} {position['name']}
💰 持仓价: ¥{entry_price:.2f}
📉 当前价: ¥{current_price:.2f}
📊 亏损: {loss_percent * 100:.2f}%
🔍 原因: 触发止损阈值 ({self.stop_loss_percent * 100:.1f}%)

⏰ 执行时间: {datetime.now().strftime('%H:%M:%S')}
"""

                self.sender.send_message(
                    title="🚨 止损操作执行",
                    content=content,
                    msg_type="markdown",
                    level="urgent"
                )

                return stop_loss_order
            return None
        except Exception as e:
            print(f"[RiskAgent] 执行止损失败: {e}")
            return None

    def adjust_position(self, position, risk_level):
        """调整仓位"""
        try:
            current_quantity = position['quantity']
            current_price = position['current_price']
            current_value = current_quantity * current_price

            # 根据风险等级调整仓位
            if risk_level == "高":
                # 降低仓位50%
                new_quantity = int(current_quantity * 0.5)
            elif risk_level == "中":
                # 降低仓位20%
                new_quantity = int(current_quantity * 0.8)
            else:
                # 保持仓位
                return position

            new_value = new_quantity * current_price
            adjustment = {
                "symbol": position['symbol'],
                "name": position['name'],
                "old_quantity": current_quantity,
                "new_quantity": new_quantity,
                "old_value": current_value,
                "new_value": new_value,
                "risk_level": risk_level,
                "timestamp": datetime.now().isoformat()
            }

            # 发送仓位调整通知
            content = f"""
📊 仓位调整

📈 股票: {position['symbol']} {position['name']}
🔄 风险等级: {risk_level}
📊 原仓位: {current_quantity}股 (¥{current_value:.2f})
📊 新仓位: {new_quantity}股 (¥{new_value:.2f})

⏰ 执行时间: {datetime.now().strftime('%H:%M:%S')}
"""

            self.sender.send_message(
                title="📊 仓位调整",
                content=content,
                msg_type="markdown",
                level="info"
            )

            return adjustment
        except Exception as e:
            print(f"[RiskAgent] 调整仓位失败: {e}")
            return position

    def generate_risk_report(self):
        """生成风险报告"""
        try:
            # 模拟数据
            market_risk = self.assess_market_risk({})
            position_risk = self.assess_position_risk(self.positions)

            # 构造报告
            content = f"""
📋 风险报告

⏰ 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 市场风险
📊 波动率: {market_risk['volatility']:.2f}
💰 资金流向风险: {market_risk['capital_risk']:.2f}
📈 总风险: {market_risk['total_risk']:.2f}
📋 风险等级: {market_risk['risk_level']}

## 持仓风险
💰 总持仓价值: ¥{position_risk['total_value']:.2f}
📈 总风险: {position_risk['total_risk']:.2f}
📋 整体风险等级: {position_risk['overall_risk_level']}

## 持仓详情
"""

            # 添加持仓详情
            for symbol, risk in position_risk['positions'].items():
                risk_icon = "🟢" if risk['risk_level'] == "低" else "🟡" if risk['risk_level'] == "中" else "🔴"
                content += f"- **{symbol} {risk['name']}**: {risk_icon} 风险等级: {risk['risk_level']}, 亏损: {risk['loss_percent']}%, 价值: ¥{risk['position_value']:.2f}\n"

            # 发送风险报告
            self.sender.send_message(
                title="📋 风险报告",
                content=content,
                msg_type="markdown",
                level="info"
            )

            # 保存风险报告
            report_file = os.path.join(self.data_dir, f"risk_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "market_risk": market_risk,
                    "position_risk": position_risk
                }, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"[RiskAgent] 生成风险报告失败: {e}")
            return False

    def check_circuit_breaker(self, market_data):
        """检查熔断机制"""
        try:
            market_risk = self.assess_market_risk(market_data)
            
            if market_risk['risk_level'] == "高":
                # 触发熔断
                content = f"""
🚨 市场风险熔断

📊 市场风险等级: 高
📈 总风险: {market_risk['total_risk']:.2f}

🔍 熔断措施:
- 暂停所有交易
- 等待市场稳定
- 15分钟后重新评估

⏰ 触发时间: {datetime.now().strftime('%H:%M:%S')}
"""

                self.sender.send_message(
                    title="🚨 市场风险熔断",
                    content=content,
                    msg_type="markdown",
                    level="urgent"
                )
                return True
            return False
        except Exception as e:
            print(f"[RiskAgent] 检查熔断机制失败: {e}")
            return False

    def run(self, interval=600):  # 默认10分钟
        """运行Agent"""
        print(f"风险控制Agent启动，间隔: {interval}秒")

        while True:
            try:
                current_hour = datetime.now().hour

                # 只在交易时段运行
                if 9 <= current_hour < 15:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 检查风险...")
                    
                    # 生成风险报告
                    self.generate_risk_report()

                    # 检查熔断机制
                    self.check_circuit_breaker({})

                    # 检查持仓风险并执行止损
                    for symbol, position in self.positions.items():
                        stop_loss_order = self.execute_stop_loss(position)
                        if stop_loss_order:
                            print(f"执行止损: {symbol}")

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n风险控制Agent停止")
                break
            except Exception as e:
                print(f"风险控制错误: {e}")
                time.sleep(60)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='风险控制Agent')
    parser.add_argument('--test', action='store_true', help='测试模式：运行一次风险评估并打印结果')
    parser.add_argument('--interval', type=int, default=600, help='检查间隔（秒），默认600秒（10分钟）')
    args = parser.parse_args()

    agent = RiskControllerAgent()

    if args.test:
        print("=== 风险控制Agent测试模式 ===")
        
        # 测试市场风险评估
        print("\n1. 测试市场风险评估:")
        market_risk = agent.assess_market_risk({})
        print(f"   市场风险: {market_risk}")
        
        # 测试持仓风险评估
        print("\n2. 测试持仓风险评估:")
        test_positions = {
            "002594": {
                "symbol": "002594",
                "name": "比亚迪",
                "current_price": 210.0,
                "entry_price": 225.0,
                "quantity": 100
            },
            "300750": {
                "symbol": "300750",
                "name": "宁德时代",
                "current_price": 230.0,
                "entry_price": 220.0,
                "quantity": 50
            }
        }
        position_risk = agent.assess_position_risk(test_positions)
        print(f"   持仓风险: {position_risk}")
        
        # 测试止损操作
        print("\n3. 测试止损操作:")
        stop_loss_result = agent.execute_stop_loss(test_positions["002594"])
        print(f"   止损结果: {stop_loss_result}")
        
        # 测试风险报告
        print("\n4. 测试风险报告:")
        agent.positions = test_positions
        report_result = agent.generate_risk_report()
        print(f"   风险报告生成: {'成功' if report_result else '失败'}")
        
        print("\n测试完成，退出。")
    else:
        print(f"风险控制Agent启动，间隔: {args.interval}秒")
        agent.run(interval=args.interval)