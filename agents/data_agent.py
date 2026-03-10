#!/usr/bin/env python3
"""
数据采集Agent
负责收集市场数据并推送到钉钉
"""

import time
import json
import sys
from datetime import datetime
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dingtalk_sender import DingTalkSender

# 尝试导入akshare，如果失败则使用模拟数据
try:
    import akshare as ak
    import pandas as pd
    AKSHARE_AVAILABLE = True
    print("[DataAgent] akshare可用，将使用真实数据源")
except ImportError:
    AKSHARE_AVAILABLE = False
    print("[DataAgent] akshare不可用，将使用模拟数据")

class DataCollectorAgent:
    def __init__(self, use_real_data=True):
        self.sender = DingTalkSender()
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(project_root, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.use_real_data = use_real_data and AKSHARE_AVAILABLE
        if self.use_real_data:
            print("[DataAgent] 配置为使用真实市场数据")
        else:
            print("[DataAgent] 配置为使用模拟数据")

    def collect_market_data(self):
        """收集市场数据（优先使用akshare真实数据）"""
        current_time = datetime.now().strftime("%H:%M:%S")

        # 如果不使用真实数据或akshare不可用，则返回模拟数据
        if not self.use_real_data:
            return self._get_mock_data(current_time)

        try:
            # 1. 获取热点板块（涨幅前5）
            hot_sectors = self._get_hot_sectors()

            # 2. 获取资金流向
            capital_flow = self._get_capital_flow()

            return {
                "timestamp": current_time,
                "hot_sectors": hot_sectors,
                "capital_flow": capital_flow
            }
        except Exception as e:
            print(f"[DataAgent] 获取真实数据失败: {e}")
            print("回退到模拟数据")
            return self._get_mock_data(current_time)

    def _get_mock_data(self, current_time):
        """返回模拟数据（降级用）"""
        hot_sectors = [
            {"name": "人工智能", "change": 3.5, "leader": "002230 科大讯飞"},
            {"name": "半导体", "change": 2.8, "leader": "688981 中芯国际"},
            {"name": "新能源车", "change": 2.3, "leader": "002594 比亚迪"},
            {"name": "金融科技", "change": 1.8, "leader": "300059 东方财富"},
            {"name": "消费电子", "change": 1.5, "leader": "002475 立讯精密"}
        ]

        capital_flow = {
            "northbound_in": 1.2,  # 北向资金流入（亿）
            "main_net_in": 3.5,    # 主力资金净流入（亿）
            "retail_net_in": -0.8  # 散户资金净流入（亿）
        }

        return {
            "timestamp": current_time,
            "hot_sectors": hot_sectors,
            "capital_flow": capital_flow
        }

    def _get_hot_sectors(self):
        """使用akshare获取热点板块（涨幅前5）"""
        try:
            sector_df = ak.stock_sector_spot()
            if sector_df.empty:
                raise ValueError("板块数据为空")

            # 确保有涨跌幅列
            if '涨跌幅' not in sector_df.columns:
                # 尝试其他可能的列名
                if '涨幅' in sector_df.columns:
                    change_col = '涨幅'
                else:
                    change_col = sector_df.columns[5]  # 假设第6列为涨跌幅
            else:
                change_col = '涨跌幅'

            # 转换为数值，处理百分号
            sector_df[change_col] = sector_df[change_col].astype(str).str.replace('%', '').astype(float)

            # 按涨跌幅降序排序，取前5
            top_sectors = sector_df.nlargest(5, change_col)

            hot_sectors = []
            for _, row in top_sectors.iterrows():
                sector_name = row['板块'] if '板块' in row else row.iloc[1]  # 板块名称列
                change = round(float(row[change_col]), 2)
                # 获取领涨股（假设股票代码列存在）
                leader_code = row['股票代码'] if '股票代码' in row else ''
                leader_name = row['股票名称'] if '股票名称' in row else ''
                leader = f"{leader_code} {leader_name}".strip()
                if not leader:
                    leader = "未知"

                hot_sectors.append({
                    "name": sector_name,
                    "change": change,
                    "leader": leader
                })

            return hot_sectors
        except Exception as e:
            print(f"[DataAgent] 获取热点板块失败: {e}")
            # 返回模拟板块
            return self._get_mock_data(datetime.now().strftime("%H:%M:%S"))["hot_sectors"]

    def _get_capital_flow(self):
        """使用akshare获取资金流向数据"""
        try:
            capital_flow = {
                "northbound_in": 0.0,
                "main_net_in": 0.0,
                "retail_net_in": 0.0
            }

            # 1. 北向资金 (沪深港通)
            try:
                hsgt_summary = ak.stock_hsgt_fund_flow_summary_em()
                if not hsgt_summary.empty:
                    # 筛选北向资金（资金方向为北向）
                    northbound = hsgt_summary[hsgt_summary['资金方向'] == '北向']
                    if not northbound.empty:
                        # 成交净买额（元），转换为亿
                        net_buy = northbound.iloc[-1]['成交净买额']
                        if pd.notna(net_buy):
                            capital_flow['northbound_in'] = round(float(net_buy) / 100000000, 2)
            except Exception as e:
                print(f"[DataAgent] 北向资金获取失败: {e}")

            # 2. 主力资金和散户资金
            try:
                market_flow = ak.stock_market_fund_flow()
                if not market_flow.empty:
                    latest = market_flow.iloc[-1]
                    # 主力净流入-净额（元），转换为亿
                    main_net = latest['主力净流入-净额']
                    if pd.notna(main_net):
                        capital_flow['main_net_in'] = round(float(main_net) / 100000000, 2)

                    # 小单净流入-净额（元）作为散户资金，转换为亿
                    retail_net = latest['小单净流入-净额']
                    if pd.notna(retail_net):
                        capital_flow['retail_net_in'] = round(float(retail_net) / 100000000, 2)
            except Exception as e:
                print(f"[DataAgent] 市场资金流向获取失败: {e}")

            return capital_flow
        except Exception as e:
            print(f"[DataAgent] 获取资金流向失败: {e}")
            # 返回模拟资金流向
            return self._get_mock_data(datetime.now().strftime("%H:%M:%S"))["capital_flow"]

    def send_market_summary(self):
        """发送市场总结到钉钉"""
        data = self.collect_market_data()

        # 构造消息内容
        content = f"""
📊 市场数据更新
⏰ 时间: {data['timestamp']}

🔥 热点板块:
"""
        for sector in data['hot_sectors']:
            change_icon = "🟢" if sector['change'] > 0 else "🔴"
            content += f"- **{sector['name']}**: {change_icon} {sector['change']}% ({sector['leader']})\n"

        content += f"""
💰 资金流向:
- 北向资金: {data['capital_flow']['northbound_in']}亿
- 主力资金: {data['capital_flow']['main_net_in']}亿
- 散户资金: {data['capital_flow']['retail_net_in']}亿

💡 操作提示:
关注资金持续流入的板块
"""

        # 发送消息
        success = self.sender.send_message(
            title="📈 市场数据更新",
            content=content,
            msg_type="markdown",
            level="info"
        )

        # 保存数据
        data_file = os.path.join(self.data_dir, f"market_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return success

    def run(self, interval=300):  # 默认5分钟
        """运行Agent"""
        print(f"数据采集Agent启动，间隔: {interval}秒")

        while True:
            try:
                current_hour = datetime.now().hour

                # 只在交易时段运行
                if 9 <= current_hour < 15:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 收集市场数据...")
                    self.send_market_summary()

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n数据采集Agent停止")
                break
            except Exception as e:
                print(f"数据采集错误: {e}")
                time.sleep(60)  # 错误后等待1分钟

if __name__ == "__main__":
    agent = DataCollectorAgent()
    agent.run(interval=300)  # 5分钟间隔
