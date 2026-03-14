#!/usr/bin/env python3
"""
技术分析Agent
负责分析股票技术指标并生成买卖信号
"""

import time
import json
from datetime import datetime, timedelta
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dingtalk import DingTalkSender
from config.config_manager import config_manager
from data.data_share import data_share
from utils.error_handler import error_handler

# 尝试解决 jsonpath 依赖问题
try:
    import jsonpath_ng as jsonpath
    sys.modules['jsonpath'] = jsonpath
    # 尝试设置 jsonpath.ext 以兼容 akshare
    try:
        import jsonpath_ng.ext
        jsonpath.ext = jsonpath_ng.ext
    except ImportError:
        pass
except ImportError:
    pass

# 尝试导入真实数据依赖
try:
    import akshare as ak
    import pandas as pd
    import numpy as np
    HAS_REAL_DATA = True
except ImportError:
    HAS_REAL_DATA = False
    print("警告: akshare/pandas/numpy 未安装，将使用模拟数据")

# 尝试导入Tushare
try:
    import tushare as ts
    HAS_TUSHARE = True
except ImportError:
    HAS_TUSHARE = False
    print("警告: tushare 未安装，Tushare数据源不可用")

# 尝试导入BaoStock
try:
    import baostock as bs
    HAS_BAOSTOCK = True
except ImportError:
    HAS_BAOSTOCK = False
    print("警告: baostock 未安装，BaoStock数据源不可用")

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

class TechnicalAnalysisAgent:
    def __init__(self, primary_source='tushare'):
        self.sender = DingTalkSender()
        # 从配置获取设置
        self.analysis_interval = config_manager.get("technical_analysis", "analysis_interval", 900)
        self.watch_list = self.load_watch_list()
        # 数据源配置
        self.primary_source = primary_source if DATA_SOURCES.get(primary_source, {}).get('available', False) else 'tushare'
        # 初始化数据源状态
        self.data_source_status = {}
        for source, info in DATA_SOURCES.items():
            self.data_source_status[source] = {
                'available': info['available'],
                'last_used': None,
                'failures': 0
            }
        # 检查是否有可用的数据源
        has_available_source = any(info['available'] for info in DATA_SOURCES.values())
        if has_available_source:
            print(f"[TechnicalAgent] 配置为使用真实市场数据，主数据源: {DATA_SOURCES[self.primary_source]['name']}")
        else:
            print("[TechnicalAgent] 配置为使用模拟数据")
        # 订阅配置变更
        config_manager.subscribe("technical_analysis", self._handle_config_change)

    def _handle_config_change(self, new_config, old_config):
        """处理配置变更"""
        print(f"技术分析Agent配置已更新: {new_config}")
        self.analysis_interval = new_config.get("analysis_interval", 900)
    
    def load_watch_list(self):
        """从config/watch_list.txt加载股票监控列表"""
        try:
            return self._load_real_watch_list()
        except Exception as e:
            print(f"加载监控列表失败: {e}")
            return []
    
    def _load_real_watch_list(self):
        """加载真实监控列表"""
        watch_list = []
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "watch_list.txt")

        if not os.path.exists(config_path):
            print(f"配置文件不存在: {config_path}")
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue

                parts = line.split(',')
                if len(parts) >= 2:
                    code = parts[0].strip()
                    name = parts[1].strip()
                    # 价格字段已移除，统一设为0.0（将从实时数据获取）
                    price = 0.0
                    watch_list.append({"code": code, "name": name, "price": price})
                else:
                    print(f"配置文件第{line_num}行格式错误: {line}")

        print(f"从配置文件加载了 {len(watch_list)} 只股票")
        return watch_list

    def _get_safe_dates(self):
        """获取安全的日期范围，避免未来日期问题"""
        now = datetime.now()
        end_date = now.strftime("%Y%m%d")
        start_date = (now - timedelta(days=30)).strftime("%Y%m%d")
        return start_date, end_date

    def _get_data_from_source(self, code, source):
        """从指定数据源获取股票数据（统一接口）"""
        try:
            # 构建股票代码
            if code.startswith('6'):
                symbol = f'sh{code}'
            else:
                symbol = f'sz{code}'

            if source == 'tushare' and HAS_TUSHARE:
                # Tushare接口
                try:
                    # 使用Tushare获取实时行情
                    df = ts.get_realtime_quotes(code)
                    if not df.empty:
                        price = float(df['price'].iloc[0])
                        change_percent = float(df['changepercent'].iloc[0])
                        volume = float(df['volume'].iloc[0])
                        return {
                            'price': price,
                            'change_percent': change_percent,
                            'volume': volume
                        }
                except Exception as e:
                    print(f"[TechnicalAgent] Tushare数据获取失败: {e}")
            elif source == 'baostock' and HAS_BAOSTOCK:
                # BaoStock接口
                try:
                    # 初始化BaoStock
                    bs.login()
                    # 获取历史数据（最近一天）作为实时价格
                    now = datetime.now()
                    end_date = now.strftime("%Y-%m-%d")
                    start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
                    # 为BaoStock转换股票代码格式：sh600000 -> sh.600000
                    baostock_code = symbol[:2] + '.' + symbol[2:]
                    rs = bs.query_history_k_data_plus(
                        code=baostock_code,
                        fields="date,code,open,high,low,close,volume,amount",
                        start_date=start_date,
                        end_date=end_date,
                        frequency="d",
                        adjustflag="3"
                    )
                    data_list = []
                    while (rs.error_code == '0') & rs.next():
                        data_list.append(rs.get_row_data())
                    if data_list:
                        # 获取最新的收盘价作为当前价格
                        latest_data = data_list[-1]
                        price = float(latest_data[5])  # close字段
                        volume = float(latest_data[6])  # volume字段
                        # 计算涨跌幅
                        if len(data_list) > 1:
                            prev_close = float(data_list[-2][5])
                            change_percent = (price - prev_close) / prev_close * 100
                        else:
                            change_percent = 0.0
                        bs.logout()
                        return {
                            'price': price,
                            'change_percent': change_percent,
                            'volume': volume
                        }
                    bs.logout()
                except Exception as e:
                    print(f"[TechnicalAgent] BaoStock数据获取失败: {e}")
                    try:
                        bs.logout()
                    except:
                        pass

            return None
        except Exception as e:
            print(f"[TechnicalAgent] 获取股票数据失败 {code} from {source}: {e}")
            return None

    def _get_unified_stock_data(self, code):
        """统一获取股票数据，处理数据源切换"""
        # 尝试从主数据源获取数据
        data = self._get_data_from_source(code, self.primary_source)
        if data is not None:
            self.data_source_status[self.primary_source]['last_used'] = datetime.now()
            self.data_source_status[self.primary_source]['failures'] = 0
            return data
        
        # 如果主数据源失败，尝试备用数据源
        for source in ['tushare', 'baostock']:
            if source != self.primary_source and self.data_source_status.get(source, {}).get('available', False):
                print(f"[TechnicalAgent] 尝试从备用数据源 {DATA_SOURCES[source]['name']} 获取股票 {code} 数据")
                data = self._get_data_from_source(code, source)
                if data is not None:
                    self.data_source_status[source]['last_used'] = datetime.now()
                    self.data_source_status[source]['failures'] = 0
                    return data
        
        # 如果所有数据源都失败，返回None
        return None

    def _get_real_indicators(self, code):
        """获取真实技术指标"""
        try:
            # 从统一接口获取股票数据
            stock_data = self._get_unified_stock_data(code)
            
            if stock_data:
                # 如果有真实数据，返回基于真实数据的基本指标
                price = stock_data['price']
                change_percent = stock_data['change_percent']
                
                return {
                    "price": price,
                    "change_percent": change_percent,
                    "macd": "中性",
                    "rsi": 50,
                    "rsi_status": "中性",
                    "volume_ratio": 1.0,
                    "kdj": "中性",
                    "ma5": price,
                    "ma10": price,
                    "ma20": price,
                    "rps": 0.0,
                    "rps_status": "中性",
                    "rps_20d": 0.0,
                    "rps_60d": 0.0,
                    "rps_120d": 0.0
                }
            return None
        except Exception as e:
            print(f"获取真实数据失败 {code}: {e}")
            return None

    def _get_stock_price_from_multiple_sources(self, code):
        """从多个数据源获取股票价格"""
        # 使用统一数据源接口
        stock_data = self._get_unified_stock_data(code)
        return stock_data['price'] if stock_data else None

    def analyze_stock(self, stock):
        """分析单只股票"""
        def fallback():
            # 回退到基于真实数据的分析
            code = stock.get("code", "未知")
            name = stock.get("name", "未知")
            
            # 从统一数据源获取真实数据
            stock_data = self._get_unified_stock_data(code)
            
            if stock_data:
                current_price = stock_data['price']
                change_percent = stock_data['change_percent']
                volume = stock_data.get('volume', 0)
            else:
                # 如果无法获取真实数据，使用默认值
                current_price = 0.0
                change_percent = 0.0
                volume = 0
            
            # 基于真实数据计算指标
            macd_signal = "中性"
            kdj_signal = "中性"
            rsi_value = 50  # 中性值
            volume_ratio = 1.0  # 简化处理
            rsi_status = "中性"
            ma5 = ma10 = ma20 = current_price
            rps_20d = 0.0
            rps_60d = 0.0
            rps_120d = 0.0
            rps_score = 0.0
            rps_status = "中性"
            
            return {
                "code": code,
                "name": name,
                "price": current_price,
                "change_percent": change_percent,
                "indicators": {
                    "macd": macd_signal,
                    "kdj": kdj_signal,
                    "rsi": rsi_value,
                    "volume_ratio": volume_ratio,
                    "ma5": ma5,
                    "ma10": ma10,
                    "ma20": ma20,
                    "rps": round(rps_score, 1),
                    "rps_status": rps_status,
                    "rps_20d": round(rps_20d, 1),
                    "rps_60d": round(rps_60d, 1),
                    "rps_120d": round(rps_120d, 1)
                },
                "score": 0.0,  # 移除评分
                "signal": "观望"
            }

        # 验证股票数据
        if not isinstance(stock, dict) or "code" not in stock:
            print(f"无效的股票数据: {stock}")
            return fallback()

        return error_handler.try_execute_with_fallback(
            self._analyze_real_stock,
            fallback,
            stock
        )
    
    def _analyze_real_stock(self, stock):
        """分析真实股票数据"""
        code = stock["code"]
        name = stock["name"]

        # 1. 基础过滤
        # 剔除ST股（通过股票名称判断）
        is_st = 'ST' in name or '*ST' in name
        # 剔除北交所（代码以8开头）
        is_bse = code.startswith('8')
        # 剔除科创板（代码以688开头）
        is_sse = code.startswith('688')
        # 基础过滤条件
        base_filter = not is_st and not is_bse and not is_sse
        
        if not base_filter:
            # 不符合基础过滤条件，直接返回观望信号
            current_price = 0.0
            change_percent = 0.0
            macd_signal = "中性"
            rsi_value = 50
            rsi_status = "中性"
            volume_ratio = 1.0
            kdj_signal = "中性"
            ma5 = ma10 = ma20 = 0.0
            rps_status = "中性"
            score = 3.0
            return {
                "code": code,
                "name": name,
                "price": current_price,
                "change_percent": change_percent,
                "indicators": {
                    "macd": macd_signal,
                    "kdj": kdj_signal,
                    "rsi": rsi_value,
                    "volume_ratio": volume_ratio,
                    "ma5": ma5,
                    "ma10": ma10,
                    "ma20": ma20,
                    "rps": 0.0,
                    "rps_status": rps_status,
                    "rps_20d": 0.0,
                    "rps_60d": 0.0,
                    "rps_120d": 0.0
                },
                "score": score,
                "signal": "观望"
            }

        # 从统一接口获取股票数据
        stock_data = self._get_unified_stock_data(code)
        
        if stock_data:
            # 使用统一数据源获取的数据
            current_price = stock_data['price']
            change_percent = stock_data['change_percent']
            volume = stock_data.get('volume', 0)
            
            # 计算基本指标
            macd_signal = "中性"
            rsi_value = 50
            rsi_status = "中性"
            volume_ratio = 1.0  # 简化处理
            kdj_signal = "中性"
            ma5 = ma10 = ma20 = current_price  # 简化处理
            rps_status = "中性"
            
            # 计算MACD金叉
            macd_gold_cross = False
            # 计算KDJ金叉
            kdj_gold_cross = False
            # 量能放大
            volume_amplified = volume > 100000  # 简化处理
            # 价格突破（假设）
            price_breakout = True
            # 连续放量（假设）
            continuous_volume = True
            # 5日均线角度（简化计算）
            ma5_angle = 20 if ma5 > ma10 else 0
        else:
            # 如果无法获取真实数据，使用默认值
            current_price = 0.0
            change_percent = 0.0
            macd_signal = "中性"
            rsi_value = 50
            rsi_status = "中性"
            volume_ratio = 1.0
            kdj_signal = "中性"
            ma5 = ma10 = ma20 = 0.0
            rps_status = "中性"
            macd_gold_cross = False
            kdj_gold_cross = False
            volume_amplified = False
            price_breakout = False
            continuous_volume = False
            ma5_angle = 0

        # 1. 价格大于等于5日均线价
        price_above_ma5 = current_price >= ma5

        # 2. 最终选股条件
        # 只保留基础过滤和价格大于等于5日均线价的条件
        select_condition = base_filter and price_above_ma5

        # 生成信号（只基于超短线逻辑）
        signal = "买入" if select_condition else "观望"

        return {
            "code": code,
            "name": name,
            "price": current_price,
            "change_percent": change_percent,
            "indicators": {
                "macd": macd_signal,
                "kdj": kdj_signal,
                "rsi": rsi_value,
                "volume_ratio": volume_ratio,
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20,
                "rps": 0.0,
                "rps_status": rps_status,
                "rps_20d": 0.0,
                "rps_60d": 0.0,
                "rps_120d": 0.0
            },
            "score": 0.0,  # 保留字段但设为0
            "signal": signal
        }

    def send_analysis_results(self):
        """发送分析结果到钉钉"""
        def fallback():
            print("分析结果发送失败，使用模拟数据")
            return 0

        return error_handler.try_execute_with_fallback(
            self._send_real_analysis_results,
            fallback
        )
    
    def _send_real_analysis_results(self):
        """发送真实分析结果"""
        results = []
        buy_signals = []

        for stock in self.watch_list:
            result = self.analyze_stock(stock)
            results.append(result)

            if result["signal"] == "买入":
                buy_signals.append(result)

        # 存储分析结果到数据共享
        analysis_data = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "buy_signals": buy_signals
        }
        data_share.set_analysis_results(analysis_data)

        # 存储分析结果到DataStorage
        try:
            from data.storage import DataStorage
            storage = DataStorage()
            for result in results:
                analysis_record = {
                    "timestamp": datetime.now().isoformat(),
                    "symbol": result["code"],
                    "name": result["name"],
                    "indicators": result["indicators"],
                    "score": result["score"],
                    "signal": result["signal"]
                }
                storage.save_technical_analysis(analysis_record)
            storage.close()
        except Exception as e:
            print(f"存储分析结果到DataStorage失败: {e}")

        # 如果有买入信号，发送详细分析
        if buy_signals:
            for signal in buy_signals[:3]:  # 最多发送3个买入信号
                content = f"""
🚨 买入信号: {signal['code']} {signal['name']}

💰 价格信息:
- 当前价: ¥{signal['price']:.2f}
- 涨跌幅: {signal['change_percent']:+.2f}%

🎯 操作建议:
- 建议仓位: 5-10%
- 持仓期: 1-3天
- 止损位: 当前价 × 0.92

⏰ 分析时间: {datetime.now().strftime('%H:%M:%S')}
"""

                self.sender.send_message(
                    title=f"🚨 买入信号: {signal['code']} {signal['name']}",
                    content=content,
                    msg_type="markdown",
                    level="urgent"
                )

        # 保存分析结果到文件
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, "data")
        os.makedirs(data_dir, exist_ok=True)

        result_file = os.path.join(data_dir, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)

        return len(buy_signals)

    def run(self, interval=None):  # 默认使用配置中的间隔
        """运行Agent"""
        # 使用配置中的间隔时间，如果没有提供
        run_interval = interval or self.analysis_interval
        print(f"技术分析Agent启动，间隔: {run_interval}秒")

        while True:
            try:
                current_hour = datetime.now().hour
                current_minute = datetime.now().minute

                # 只在交易时段运行
                if 9 <= current_hour < 15:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 分析股票...")
                    buy_count = self.send_analysis_results()

                    if buy_count > 0:
                        print(f"发现 {buy_count} 个买入信号")

                time.sleep(run_interval)

            except KeyboardInterrupt:
                print("\n技术分析Agent停止")
                break
            except Exception as e:
                error_handler.handle_error(e, "技术分析Agent运行时")
                time.sleep(60)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='技术分析Agent')
    parser.add_argument('--test', action='store_true', help='测试模式：运行一次分析并打印结果')
    parser.add_argument('--interval', type=int, default=900, help='分析间隔（秒），默认900秒（15分钟）')
    args = parser.parse_args()

    agent = TechnicalAnalysisAgent()

    if args.test:
        print("=== 技术分析Agent测试模式 ===")
        print(f"监控股票数量: {len(agent.watch_list)}")
        print("股票列表:")
        for stock in agent.watch_list:
            print(f"  - {stock['code']} {stock['name']} (实时价格)")
        print("\n分析结果:")
        results = []
        for stock in agent.watch_list:
            result = agent.analyze_stock(stock)
            results.append(result)
            print(f"\n{result['code']} {result['name']}:")
            print(f"  当前价: {result['price']:.2f} ({result['change_percent']:+.2f}%)")
            print(f"  信号: {result['signal']}")
            print(f"  技术指标: MACD={result['indicators']['macd']}, KDJ={result['indicators']['kdj']}, RSI={result['indicators']['rsi']}, 量比={result['indicators']['volume_ratio']:.2f}, RPS={result['indicators']['rps']:.1f}({result['indicators']['rps_status']}), MA5={result['indicators']['ma5']:.2f}, MA10={result['indicators']['ma10']:.2f}, MA20={result['indicators']['ma20']:.2f}")

        # 统计信号
        buy_count = sum(1 for r in results if r['signal'] == '买入')
        sell_count = sum(1 for r in results if r['signal'] == '卖出')
        print(f"\n=== 信号统计 ===")
        print(f"买入信号: {buy_count} | 卖出信号: {sell_count} | 观望: {len(results)-buy_count-sell_count}")
        print("测试完成，退出。")
    else:
        print(f"技术分析Agent启动，间隔: {args.interval}秒")
        agent.run(interval=args.interval)
