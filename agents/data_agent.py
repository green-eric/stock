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
from dingtalk import DingTalkSender
from config.config_manager import config_manager
from data.data_share import data_share
from utils.error_handler import error_handler

# 尝试导入Tushare和BaoStock
# 尝试导入Tushare
try:
    import tushare as ts
    HAS_TUSHARE = True
    print("[DataAgent] Tushare可用，将使用真实数据源")
except ImportError:
    HAS_TUSHARE = False
    print("[DataAgent] Tushare不可用")

# 尝试导入BaoStock
try:
    import baostock as bs
    HAS_BAOSTOCK = True
    print("[DataAgent] BaoStock可用，将使用真实数据源")
except ImportError:
    HAS_BAOSTOCK = False
    print("[DataAgent] BaoStock不可用")

# 数据源配置
DATA_SOURCES = {
    'tushare': {
        'name': 'Tushare',
        'available': HAS_TUSHARE
    },
    'baostock': {
        'name': 'BaoStock',
        'available': HAS_BAOSTOCK
    }
}

class DataCollectorAgent:
    def __init__(self, primary_source='tushare'):
        self.sender = DingTalkSender()
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(project_root, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        # 从配置获取设置
        self.primary_source = primary_source if DATA_SOURCES.get(primary_source, {}).get('available', False) else 'tushare'
        self.check_interval = config_manager.get("data_collector", "check_interval", 300)
        print(f"[DataAgent] 配置为使用真实市场数据，主数据源: {DATA_SOURCES[self.primary_source]['name']}")
        
        # 初始化数据源状态
        self.data_source_status = {}
        for source, info in DATA_SOURCES.items():
            self.data_source_status[source] = {
                'available': info['available'],
                'last_used': None,
                'failures': 0
            }

    def collect_market_data(self):
        """收集市场数据（优先使用主数据源，失败时自动切换）"""
        current_time = datetime.now().strftime("%H:%M:%S")

        # 尝试从主数据源获取数据
        data = self._get_data_from_source(self.primary_source, current_time)
        
        # 如果主数据源失败，尝试其他数据源
        if not data:
            for source in ['tushare', 'baostock']:
                if source != self.primary_source and self.data_source_status.get(source, {}).get('available', False):
                    print(f"尝试从备用数据源 {DATA_SOURCES[source]['name']} 获取数据")
                    data = self._get_data_from_source(source, current_time)
                    if data:
                        break
        
        # 验证数据完整性
        if data and isinstance(data, dict):
            if 'hot_sectors' not in data or data['hot_sectors'] is None:
                data['hot_sectors'] = []
            if 'capital_flow' not in data:
                data['capital_flow'] = {}
            if 'data_source' not in data:
                data['data_source'] = self.primary_source
            data_share.set_market_data(data)
            return data
        else:
            # 如果数据无效，返回空数据
            print("数据无效，返回空数据")
            data = {
                "timestamp": current_time,
                "hot_sectors": [],
                "capital_flow": {
                    "northbound_in": 0.0,
                    "main_net_in": 0.0,
                    "retail_net_in": 0.0
                },
                "data_source": self.primary_source
            }
            data_share.set_market_data(data)
            return data
    
    def _get_data_from_source(self, source, current_time):
        """从指定数据源获取数据"""
        def fallback():
            print(f"数据源 {DATA_SOURCES[source]['name']} 失败")
            self.data_source_status[source]['failures'] += 1
            return None
        
        try:
            if source == 'tushare' or source == 'baostock':
                # 使用真实市场数据
                data = self._get_real_market_data(current_time)
            else:
                return None
            
            if data:
                data['data_source'] = source
                self.data_source_status[source]['last_used'] = datetime.now()
                self.data_source_status[source]['failures'] = 0
            return data
        except Exception as e:
            print(f"数据源 {DATA_SOURCES[source]['name']} 出错: {e}")
            self.data_source_status[source]['failures'] += 1
            return None
    
    def _get_real_market_data(self, current_time):
        """获取真实市场数据"""
        # 1. 获取热点板块（涨幅前5）
        hot_sectors = self._get_hot_sectors()

        # 2. 获取资金流向
        capital_flow = self._get_capital_flow()

        return {
            "timestamp": current_time,
            "hot_sectors": hot_sectors,
            "capital_flow": capital_flow
        }



    def _get_hot_sectors(self):
        """获取热点板块（涨幅前5）"""
        return error_handler.try_execute(self._get_real_hot_sectors)
    
    def _get_real_hot_sectors(self):
        """获取真实热点板块数据"""
        # 尝试从Tushare获取板块数据
        if HAS_TUSHARE:
            try:
                # 使用Tushare获取行业板块数据
                industry = ts.get_industry_classified()
                if not industry.empty:
                    # 获取每个行业的涨幅
                    sectors = {}
                    for _, row in industry.iterrows():
                        code = row['code']
                        name = row['name']
                        industry_name = row['c_name']
                        
                        # 获取股票实时行情
                        try:
                            quote = ts.get_realtime_quotes(code)
                            if not quote.empty:
                                price = float(quote['price'].iloc[0])
                                pre_close = float(quote['pre_close'].iloc[0])
                                change = round((price - pre_close) / pre_close * 100, 2)
                                
                                if industry_name not in sectors or change > sectors[industry_name]['change']:
                                    sectors[industry_name] = {
                                        "name": industry_name,
                                        "change": change,
                                        "leader": f"{code} {name}"
                                    }
                        except Exception as e:
                            print(f"获取股票 {code} 行情失败: {e}")
                    
                    # 按涨幅排序，取前5
                    hot_sectors = sorted(sectors.values(), key=lambda x: x['change'], reverse=True)[:5]
                    return hot_sectors
            except Exception as e:
                print(f"Tushare获取板块数据失败: {e}")
        
        # 尝试从BaoStock获取板块数据
        if HAS_BAOSTOCK:
            try:
                # 初始化BaoStock
                bs.login()
                # 获取行业板块数据
                industry = bs.query_industry_classified()
                data_list = []
                while (industry.error_code == '0') & industry.next():
                    data_list.append(industry.get_row_data())
                bs.logout()
                
                if data_list:
                    sectors = {}
                    for row in data_list:
                        code = row[1]
                        name = row[2]
                        industry_name = row[3]
                        
                        # 获取股票历史数据作为当前价格
                        try:
                            bs.login()
                            rs = bs.query_history_k_data_plus(
                                code=code,
                                fields="date,close",
                                start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                                end_date=datetime.now().strftime("%Y-%m-%d"),
                                frequency="d",
                                adjustflag="3"
                            )
                            price_list = []
                            while (rs.error_code == '0') & rs.next():
                                price_list.append(rs.get_row_data())
                            bs.logout()
                            
                            if price_list and len(price_list) >= 2:
                                # 计算涨幅
                                current_price = float(price_list[-1][1])
                                prev_price = float(price_list[-2][1])
                                change = round((current_price - prev_price) / prev_price * 100, 2)
                                
                                if industry_name not in sectors or change > sectors[industry_name]['change']:
                                    sectors[industry_name] = {
                                        "name": industry_name,
                                        "change": change,
                                        "leader": f"{code} {name}"
                                    }
                        except Exception as e:
                            print(f"获取股票 {code} 行情失败: {e}")
                            try:
                                bs.logout()
                            except:
                                pass
                    
                    # 按涨幅排序，取前5
                    hot_sectors = sorted(sectors.values(), key=lambda x: x['change'], reverse=True)[:5]
                    return hot_sectors
            except Exception as e:
                print(f"BaoStock获取板块数据失败: {e}")
                try:
                    bs.logout()
                except:
                    pass
        
        # 如果所有数据源都失败，返回空列表
        return []

    def _get_capital_flow(self):
        """获取资金流向数据"""
        return error_handler.try_execute(self._get_real_capital_flow)
    
    def _get_real_capital_flow(self):
        """获取真实资金流向数据"""
        capital_flow = {
            "northbound_in": 0.0,
            "main_net_in": 0.0,
            "retail_net_in": 0.0
        }

        # 1. 北向资金 (沪深港通)
        def get_northbound_flow():
            # 尝试从Tushare获取北向资金数据
            if HAS_TUSHARE:
                try:
                    # 使用Tushare获取沪深港通资金流向
                    north_money = ts.get_hsgt_top10()
                    if not north_money.empty:
                        # 计算北向资金净流入
                        net_in = north_money['net_amount'].sum()
                        capital_flow['northbound_in'] = round(net_in / 100000000, 2)
                except Exception as e:
                    print(f"[DataAgent] Tushare北向资金获取失败: {e}")
            
            # 尝试从BaoStock获取北向资金数据
            if HAS_BAOSTOCK and capital_flow['northbound_in'] == 0:
                try:
                    bs.login()
                    # 获取沪深港通资金流向
                    hsgt = bs.query_hsgt_flow()
                    data_list = []
                    while (hsgt.error_code == '0') & hsgt.next():
                        data_list.append(hsgt.get_row_data())
                    bs.logout()
                    
                    if data_list:
                        # 取最新数据
                        latest = data_list[-1]
                        north_in = float(latest[1])  # 沪股通当日净流入
                        south_in = float(latest[3])  # 深股通当日净流入
                        capital_flow['northbound_in'] = round((north_in + south_in) / 10000, 2)  # 转换为亿
                except Exception as e:
                    print(f"[DataAgent] BaoStock北向资金获取失败: {e}")
                    try:
                        bs.logout()
                    except:
                        pass

        # 2. 主力资金和散户资金
        def get_market_flow():
            # 尝试从Tushare获取资金流向数据
            if HAS_TUSHARE:
                try:
                    # 使用Tushare获取大盘资金流向
                    money_flow = ts.get_money_flow('sh')  # 上证指数
                    if not money_flow.empty:
                        latest = money_flow.iloc[-1]
                        # 主力净流入
                        main_net = latest['large_net']
                        capital_flow['main_net_in'] = round(main_net / 100000000, 2)
                        # 散户资金（小单净流入）
                        retail_net = latest['small_net']
                        capital_flow['retail_net_in'] = round(retail_net / 100000000, 2)
                except Exception as e:
                    print(f"[DataAgent] Tushare市场资金流向获取失败: {e}")

        # 执行获取资金流向
        get_northbound_flow()
        get_market_flow()

        return capital_flow
    


    def send_market_summary(self):
        """发送市场总结到钉钉"""
        def send_summary():
            data = self.collect_market_data()

            # 构造消息内容
            data_source_name = DATA_SOURCES.get(data.get('data_source', 'akshare'), {}).get('name', '未知')
            content = f"""
📊 市场数据更新
⏰ 时间: {data['timestamp']}
📡 数据源: {data_source_name}

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

        return error_handler.try_execute(send_summary)

    def run(self, interval=None):  # 默认5分钟
        """运行Agent"""
        # 使用配置中的间隔时间，如果没有提供
        run_interval = interval or self.check_interval
        print(f"数据采集Agent启动，间隔: {run_interval}秒")

        while True:
            try:
                current_hour = datetime.now().hour

                # 只在交易时段运行
                if 9 <= current_hour < 15:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 收集市场数据...")
                    self.send_market_summary()

                time.sleep(run_interval)

            except KeyboardInterrupt:
                print("\n数据采集Agent停止")
                break
            except Exception as e:
                print(f"数据采集错误: {e}")
                time.sleep(60)  # 错误后等待1分钟

if __name__ == "__main__":
    agent = DataCollectorAgent()
    agent.run(interval=300)  # 5分钟间隔
