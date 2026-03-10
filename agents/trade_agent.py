#!/usr/bin/env python3
"""
交易执行Agent
负责执行买卖操作，管理交易订单
"""

import time
import json
import uuid
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dingtalk_sender import DingTalkSender

class TradeExecutorAgent:
    def __init__(self, use_simulated=True):
        self.sender = DingTalkSender()
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(project_root, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.use_simulated = use_simulated  # 是否使用模拟交易
        self.orders = {}  # 订单管理
        self.trades = []  # 交易记录
        self.balance = 1000000.0  # 模拟资金
        self.positions = {}  # 持仓

    def place_order(self, order):
        """下单"""
        try:
            # 生成订单ID
            order_id = f"ORD{uuid.uuid4().hex[:12].upper()}"
            
            # 验证订单参数
            if not all(key in order for key in ['symbol', 'name', 'side', 'price', 'quantity']):
                return {"error": "缺少必要参数"}

            # 计算交易金额
            amount = order['price'] * order['quantity']

            # 检查资金是否充足（买入时）
            if order['side'] == 'buy' and amount > self.balance:
                return {"error": "资金不足"}

            # 检查持仓是否充足（卖出时）
            if order['side'] == 'sell':
                if order['symbol'] not in self.positions or self.positions[order['symbol']]['quantity'] < order['quantity']:
                    return {"error": "持仓不足"}

            # 创建订单
            new_order = {
                "order_id": order_id,
                "symbol": order['symbol'],
                "name": order['name'],
                "side": order['side'],
                "price": order['price'],
                "quantity": order['quantity'],
                "amount": amount,
                "status": "pending",
                "timestamp": datetime.now().isoformat(),
                "strategy": order.get('strategy', 'manual'),
                "signal_id": order.get('signal_id', '')
            }

            # 存储订单
            self.orders[order_id] = new_order

            # 模拟交易执行
            if self.use_simulated:
                # 模拟订单执行
                time.sleep(0.1)  # 模拟网络延迟
                new_order['status'] = "filled"
                new_order['filled_timestamp'] = datetime.now().isoformat()
                
                # 更新资金和持仓
                if order['side'] == 'buy':
                    self.balance -= amount
                    if order['symbol'] in self.positions:
                        self.positions[order['symbol']]['quantity'] += order['quantity']
                        self.positions[order['symbol']]['entry_price'] = (
                            self.positions[order['symbol']]['entry_price'] * self.positions[order['symbol']]['quantity'] +
                            order['price'] * order['quantity']
                        ) / (self.positions[order['symbol']]['quantity'] + order['quantity'])
                    else:
                        self.positions[order['symbol']] = {
                            "symbol": order['symbol'],
                            "name": order['name'],
                            "quantity": order['quantity'],
                            "entry_price": order['price'],
                            "current_price": order['price']
                        }
                else:
                    self.balance += amount
                    self.positions[order['symbol']]['quantity'] -= order['quantity']
                    if self.positions[order['symbol']]['quantity'] == 0:
                        del self.positions[order['symbol']]

                # 记录交易
                trade = {
                    "trade_id": f"TRADE{uuid.uuid4().hex[:12].upper()}",
                    "order_id": order_id,
                    "symbol": order['symbol'],
                    "name": order['name'],
                    "side": order['side'],
                    "price": order['price'],
                    "quantity": order['quantity'],
                    "amount": amount,
                    "timestamp": new_order['filled_timestamp'],
                    "strategy": order.get('strategy', 'manual'),
                    "signal_id": order.get('signal_id', '')
                }
                self.trades.append(trade)
                self.store_trade(trade)

                # 发送交易通知
                self._send_trade_notification(trade)

            return new_order
        except Exception as e:
            print(f"[TradeAgent] 下单失败: {e}")
            return {"error": str(e)}

    def cancel_order(self, order_id):
        """撤单"""
        try:
            if order_id not in self.orders:
                return {"error": "订单不存在"}

            order = self.orders[order_id]
            if order['status'] != "pending":
                return {"error": "订单状态不允许撤单"}

            # 更新订单状态
            order['status'] = "cancelled"
            order['cancelled_timestamp'] = datetime.now().isoformat()

            # 发送撤单通知
            content = f"""
📢 订单撤单

📊 订单ID: {order_id}
📈 股票: {order['symbol']} {order['name']}
🔄 方向: {'买入' if order['side'] == 'buy' else '卖出'}
💰 价格: ¥{order['price']:.2f}
📊 数量: {order['quantity']}股

⏰ 撤单时间: {datetime.now().strftime('%H:%M:%S')}
"""

            self.sender.send_message(
                title="📢 订单撤单",
                content=content,
                msg_type="markdown",
                level="info"
            )

            return order
        except Exception as e:
            print(f"[TradeAgent] 撤单失败: {e}")
            return {"error": str(e)}

    def get_order_status(self, order_id):
        """获取订单状态"""
        try:
            if order_id not in self.orders:
                return {"error": "订单不存在"}
            return self.orders[order_id]
        except Exception as e:
            print(f"[TradeAgent] 获取订单状态失败: {e}")
            return {"error": str(e)}

    def execute_trade(self, signal):
        """执行交易"""
        try:
            # 从信号生成订单
            order = {
                "symbol": signal['code'],
                "name": signal['name'],
                "side": "buy" if signal['signal'] == "买入" else "sell",
                "price": signal['price'],
                "quantity": int(10000 / signal['price']),  # 固定金额下单
                "strategy": "technical_analysis",
                "signal_id": f"SIG{uuid.uuid4().hex[:8].upper()}"
            }

            # 执行下单
            result = self.place_order(order)
            if "error" in result:
                return result

            return result
        except Exception as e:
            print(f"[TradeAgent] 执行交易失败: {e}")
            return {"error": str(e)}

    def store_trade(self, trade):
        """存储交易记录"""
        try:
            # 保存到文件
            trade_file = os.path.join(self.data_dir, f"trade_{datetime.now().strftime('%Y%m%d')}.json")
            
            # 读取现有记录
            existing_trades = []
            if os.path.exists(trade_file):
                with open(trade_file, 'r', encoding='utf-8') as f:
                    existing_trades = json.load(f)
            
            # 添加新交易
            existing_trades.append(trade)
            
            # 保存回文件
            with open(trade_file, 'w', encoding='utf-8') as f:
                json.dump(existing_trades, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"[TradeAgent] 存储交易记录失败: {e}")
            return False

    def get_positions(self):
        """获取当前持仓"""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "balance": self.balance,
                "positions": self.positions,
                "total_value": self.balance + sum(p['quantity'] * p['current_price'] for p in self.positions.values())
            }
        except Exception as e:
            print(f"[TradeAgent] 获取持仓失败: {e}")
            return {"error": str(e)}

    def get_trade_history(self, limit=100):
        """获取交易历史"""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "trades": self.trades[-limit:]
            }
        except Exception as e:
            print(f"[TradeAgent] 获取交易历史失败: {e}")
            return {"error": str(e)}

    def _send_trade_notification(self, trade):
        """发送交易通知"""
        try:
            content = f"""
📊 交易执行

📈 股票: {trade['symbol']} {trade['name']}
🔄 方向: {'买入' if trade['side'] == 'buy' else '卖出'}
💰 价格: ¥{trade['price']:.2f}
📊 数量: {trade['quantity']}股
💰 金额: ¥{trade['amount']:.2f}

⏰ 执行时间: {datetime.fromisoformat(trade['timestamp']).strftime('%H:%M:%S')}
"""

            self.sender.send_message(
                title="📊 交易执行",
                content=content,
                msg_type="markdown",
                level="info"
            )
        except Exception as e:
            print(f"[TradeAgent] 发送交易通知失败: {e}")

    def run(self, interval=300):  # 默认5分钟
        """运行Agent"""
        print(f"交易执行Agent启动，间隔: {interval}秒")

        while True:
            try:
                current_hour = datetime.now().hour

                # 只在交易时段运行
                if 9 <= current_hour < 15:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 检查交易状态...")
                    
                    # 检查未完成订单
                    for order_id, order in list(self.orders.items()):
                        if order['status'] == "pending":
                            # 模拟订单执行
                            if self.use_simulated:
                                order['status'] = "filled"
                                order['filled_timestamp'] = datetime.now().isoformat()
                                
                                # 更新资金和持仓
                                amount = order['price'] * order['quantity']
                                if order['side'] == 'buy':
                                    self.balance -= amount
                                    if order['symbol'] in self.positions:
                                        self.positions[order['symbol']]['quantity'] += order['quantity']
                                        self.positions[order['symbol']]['entry_price'] = (
                                            self.positions[order['symbol']]['entry_price'] * self.positions[order['symbol']]['quantity'] +
                                            order['price'] * order['quantity']
                                        ) / (self.positions[order['symbol']]['quantity'] + order['quantity'])
                                    else:
                                        self.positions[order['symbol']] = {
                                            "symbol": order['symbol'],
                                            "name": order['name'],
                                            "quantity": order['quantity'],
                                            "entry_price": order['price'],
                                            "current_price": order['price']
                                        }
                                else:
                                    self.balance += amount
                                    self.positions[order['symbol']]['quantity'] -= order['quantity']
                                    if self.positions[order['symbol']]['quantity'] == 0:
                                        del self.positions[order['symbol']]

                                # 记录交易
                                trade = {
                                    "trade_id": f"TRADE{uuid.uuid4().hex[:12].upper()}",
                                    "order_id": order_id,
                                    "symbol": order['symbol'],
                                    "name": order['name'],
                                    "side": order['side'],
                                    "price": order['price'],
                                    "quantity": order['quantity'],
                                    "amount": amount,
                                    "timestamp": order['filled_timestamp'],
                                    "strategy": order.get('strategy', 'manual'),
                                    "signal_id": order.get('signal_id', '')
                                }
                                self.trades.append(trade)
                                self.store_trade(trade)

                                # 发送交易通知
                                self._send_trade_notification(trade)

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n交易执行Agent停止")
                break
            except Exception as e:
                print(f"交易执行错误: {e}")
                time.sleep(60)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='交易执行Agent')
    parser.add_argument('--test', action='store_true', help='测试模式：运行一次交易操作并打印结果')
    parser.add_argument('--interval', type=int, default=300, help='检查间隔（秒），默认300秒（5分钟）')
    args = parser.parse_args()

    agent = TradeExecutorAgent(use_simulated=True)

    if args.test:
        print("=== 交易执行Agent测试模式 ===")
        
        # 测试下单
        print("\n1. 测试下单:")
        order = {
            "symbol": "002594",
            "name": "比亚迪",
            "side": "buy",
            "price": 225.0,
            "quantity": 100
        }
        result = agent.place_order(order)
        print(f"   下单结果: {result}")
        
        # 测试获取订单状态
        print("\n2. 测试获取订单状态:")
        if "order_id" in result:
            order_status = agent.get_order_status(result["order_id"])
            print(f"   订单状态: {order_status}")
        
        # 测试获取持仓
        print("\n3. 测试获取持仓:")
        positions = agent.get_positions()
        print(f"   持仓: {positions}")
        
        # 测试卖出
        print("\n4. 测试卖出:")
        sell_order = {
            "symbol": "002594",
            "name": "比亚迪",
            "side": "sell",
            "price": 230.0,
            "quantity": 50
        }
        sell_result = agent.place_order(sell_order)
        print(f"   卖出结果: {sell_result}")
        
        # 测试获取交易历史
        print("\n5. 测试获取交易历史:")
        history = agent.get_trade_history()
        print(f"   交易历史: {history}")
        
        print("\n测试完成，退出。")
    else:
        print(f"交易执行Agent启动，间隔: {args.interval}秒")
        agent.run(interval=args.interval)