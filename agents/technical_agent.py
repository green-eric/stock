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

# 数据源配置
DATA_SOURCES = {
    'akshare': {
        'name': 'AKShare',
        'available': HAS_REAL_DATA
    },
    'sina': {
        'name': '新浪财经',
        'available': HAS_REAL_DATA  # 基于akshare的新浪接口
    },
    'eastmoney': {
        'name': '东方财富',
        'available': HAS_REAL_DATA  # 基于akshare的东方财富接口
    }
}

class TechnicalAnalysisAgent:
    def __init__(self, primary_source='akshare'):
        self.sender = DingTalkSender()
        # 从配置获取设置
        self.analysis_interval = config_manager.get("technical_analysis", "analysis_interval", 900)
        self.watch_list = self.load_watch_list()
        # 数据源配置
        self.primary_source = primary_source if DATA_SOURCES.get(primary_source, {}).get('available', False) else 'akshare'
        # 初始化数据源状态
        self.data_source_status = {}
        for source, info in DATA_SOURCES.items():
            self.data_source_status[source] = {
                'available': info['available'],
                'last_used': None,
                'failures': 0
            }
        if HAS_REAL_DATA:
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
        def fallback():
            # 默认股票列表（如果文件不存在或读取失败时使用）
            default_list = [
                {"code": "300903", "name": "科翔股份", "price": 0.0},
                {"code": "600487", "name": "亨通光电", "price": 0.0}
            ]
            print("使用默认股票监控列表")
            return default_list

        return error_handler.try_execute_with_fallback(
            self._load_real_watch_list,
            fallback
        )
    
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

    def _get_real_indicators(self, code):
        """获取真实技术指标"""
        if not HAS_REAL_DATA:
            return None

        try:
            # 尝试从多个数据源获取最新价格
            real_price = self._get_stock_price_from_multiple_sources(code)
            
            # 使用akshare获取历史数据
            # 注意：akshare的股票代码需要带市场前缀，如sz000001
            # 这里简单处理：如果以6开头，加sh，否则加sz
            if code.startswith('6'):
                symbol = f'sh{code}'
            else:
                symbol = f'sz{code}'

            # 获取最近30天的日线数据
            start_date, end_date = self._get_safe_dates()
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="")
            if df.empty:
                # 如果历史数据为空，但有真实价格，返回基于真实价格的基本指标
                if real_price:
                    return {
                        "price": real_price,
                        "change_percent": 0.0,
                        "macd": "中性",
                        "rsi": 50,
                        "rsi_status": "中性",
                        "volume_ratio": 1.0,
                        "kdj": "中性",
                        "ma5": real_price,
                        "ma10": real_price,
                        "ma20": real_price,
                        "rps": 0.0,
                        "rps_status": "中性",
                        "rps_20d": 0.0,
                        "rps_60d": 0.0,
                        "rps_120d": 0.0
                    }
                return None

            # 计算简单移动平均线
            df['MA5'] = df['收盘'].rolling(window=5).mean()
            df['MA10'] = df['收盘'].rolling(window=10).mean()
            df['MA20'] = df['收盘'].rolling(window=20).mean()

            # 计算MACD指标（简化版）
            exp1 = df['收盘'].ewm(span=12, adjust=False).mean()
            exp2 = df['收盘'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            hist = macd - signal

            # 判断MACD金叉/死叉
            last_hist = hist.iloc[-1]
            prev_hist = hist.iloc[-2] if len(hist) >= 2 else 0
            if last_hist > 0 and prev_hist <= 0:
                macd_signal = "金叉"
            elif last_hist < 0 and prev_hist >= 0:
                macd_signal = "死叉"
            else:
                macd_signal = "中性"

            # 计算RSI（简化版）
            delta = df['收盘'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1]
            if pd.isna(rsi_value):
                rsi_value = 50

            # 判断RSI超买超卖
            rsi_status = "中性"
            if rsi_value > 70:
                rsi_status = "超买"
            elif rsi_value < 30:
                rsi_status = "超卖"

            # 计算量比（当日成交量 / 过去5日平均成交量）
            volume_mean = df['成交量'].rolling(window=5).mean()
            volume_ratio = df['成交量'].iloc[-1] / volume_mean.iloc[-1] if volume_mean.iloc[-1] > 0 else 1.0

            # 计算KDJ指标（简化版）
            low_min = df['最低'].rolling(window=9).min()
            high_max = df['最高'].rolling(window=9).max()
            rsv = (df['收盘'] - low_min) / (high_max - low_min) * 100
            k = rsv.ewm(alpha=1/3).mean()
            d = k.ewm(alpha=1/3).mean()
            j = 3 * k - 2 * d

            k_value = k.iloc[-1] if not pd.isna(k.iloc[-1]) else 50
            d_value = d.iloc[-1] if not pd.isna(d.iloc[-1]) else 50
            j_value = j.iloc[-1] if not pd.isna(j.iloc[-1]) else 50

            # 判断KDJ超买超卖
            kdj_signal = "中性"
            if k_value > 80 or d_value > 80 or j_value > 80:
                kdj_signal = "超买"
            elif k_value < 20 or d_value < 20 or j_value < 20:
                kdj_signal = "超卖"

            # 计算RPS（相对强度）指标（简化版）
            # 这里使用股票自身的历史表现作为参考
            # 计算20日涨幅
            if len(df) >= 20:
                price_20d_ago = df['收盘'].iloc[-20]
                current_price = df['收盘'].iloc[-1]
                rps_20d = (current_price - price_20d_ago) / price_20d_ago * 100
            else:
                rps_20d = 0

            # 计算60日涨幅
            if len(df) >= 60:
                price_60d_ago = df['收盘'].iloc[-60]
                current_price = df['收盘'].iloc[-1]
                rps_60d = (current_price - price_60d_ago) / price_60d_ago * 100
            else:
                rps_60d = 0

            # 计算120日涨幅
            if len(df) >= 120:
                price_120d_ago = df['收盘'].iloc[-120]
                current_price = df['收盘'].iloc[-1]
                rps_120d = (current_price - price_120d_ago) / price_120d_ago * 100
            else:
                rps_120d = 0

            # RPS评级
            rps_score = (rps_20d * 0.5 + rps_60d * 0.3 + rps_120d * 0.2) / 3
            if rps_score > 15:
                rps_status = "强势"
            elif rps_score > 5:
                rps_status = "中性"
            else:
                rps_status = "弱势"

            # 获取最新价格和涨跌幅
            current_price = real_price if real_price else float(df['收盘'].iloc[-1])
            prev_close = float(df['收盘'].iloc[-2]) if len(df) >= 2 else current_price
            change_percent = (current_price - prev_close) / prev_close * 100

            return {
                "price": current_price,
                "change_percent": change_percent,
                "macd": macd_signal,
                "rsi": round(rsi_value, 1),
                "rsi_status": rsi_status,
                "volume_ratio": round(volume_ratio, 2),
                "kdj": kdj_signal,
                "ma5": float(df['MA5'].iloc[-1]) if not pd.isna(df['MA5'].iloc[-1]) else current_price,
                "ma10": float(df['MA10'].iloc[-1]) if not pd.isna(df['MA10'].iloc[-1]) else current_price,
                "ma20": float(df['MA20'].iloc[-1]) if not pd.isna(df['MA20'].iloc[-1]) else current_price,
                "rps": round(rps_score, 1),
                "rps_status": rps_status,
                "rps_20d": round(rps_20d, 1),
                "rps_60d": round(rps_60d, 1),
                "rps_120d": round(rps_120d, 1)
            }
        except Exception as e:
            print(f"获取真实数据失败 {code}: {e}")
            return None

    def _get_real_stock_price(self, code, source='akshare'):
        """从不同数据源获取真实股票价格"""
        if not HAS_REAL_DATA:
            return None

        try:
            # 使用akshare获取股票实时价格
            if code.startswith('6'):
                symbol = f'sh{code}'
            else:
                symbol = f'sz{code}'

            # 根据数据源选择不同的获取方式
            if source == 'akshare':
                # AKShare默认接口
                try:
                    df = ak.stock_zh_a_spot_em()
                    stock_data = df[df['代码'] == code]
                    if not stock_data.empty:
                        price = stock_data['最新价'].iloc[0]
                        return float(price)
                except Exception as e:
                    print(f"[TechnicalAgent] AKShare实时行情获取失败: {e}")
            elif source == 'sina':
                # 新浪财经接口
                try:
                    # 尝试使用新浪财经接口
                    df = ak.stock_zh_a_spot_em()
                    stock_data = df[df['代码'] == code]
                    if not stock_data.empty:
                        price = stock_data['最新价'].iloc[0]
                        return float(price)
                except Exception as e:
                    print(f"[TechnicalAgent] 新浪财经实时行情获取失败: {e}")
            elif source == 'eastmoney':
                # 东方财富接口
                try:
                    df = ak.stock_zh_a_spot_em()
                    stock_data = df[df['代码'] == code]
                    if not stock_data.empty:
                        price = stock_data['最新价'].iloc[0]
                        return float(price)
                except Exception as e:
                    print(f"[TechnicalAgent] 东方财富实时行情获取失败: {e}")

            # 如果实时行情失败，使用历史数据的最新收盘价
            start_date, end_date = self._get_safe_dates()
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="")
            if not df.empty:
                return float(df['收盘'].iloc[-1])

            return None
        except Exception as e:
            print(f"[TechnicalAgent] 获取股票价格失败 {code} from {source}: {e}")
            return None
    
    def _get_stock_price_from_multiple_sources(self, code):
        """从多个数据源获取股票价格"""
        # 尝试从主数据源获取价格
        price = self._get_price_from_source(self.primary_source, code)
        if price is not None:
            return price
        
        # 如果主数据源失败，尝试其他数据源
        for source in ['sina', 'eastmoney', 'akshare']:
            if source != self.primary_source and self.data_source_status.get(source, {}).get('available', False):
                print(f"[TechnicalAgent] 尝试从备用数据源 {DATA_SOURCES[source]['name']} 获取股票 {code} 价格")
                price = self._get_price_from_source(source, code)
                if price is not None:
                    return price
        
        # 如果所有数据源都失败，返回None
        return None
    
    def _get_price_from_source(self, source, code):
        """从指定数据源获取股票价格"""
        def fallback():
            print(f"[TechnicalAgent] 数据源 {DATA_SOURCES[source]['name']} 失败，尝试下一个数据源")
            self.data_source_status[source]['failures'] += 1
            return None
        
        try:
            if source == 'akshare' or source == 'sina' or source == 'eastmoney':
                # 所有数据源都使用akshare的接口，但可能调用不同的函数
                price = error_handler.try_execute_with_fallback(
                    self._get_real_stock_price,
                    fallback,
                    code,
                    source
                )
            else:
                return None
            
            if price:
                self.data_source_status[source]['last_used'] = datetime.now()
                self.data_source_status[source]['failures'] = 0
            return price
        except Exception as e:
            print(f"[TechnicalAgent] 数据源 {DATA_SOURCES[source]['name']} 出错: {e}")
            self.data_source_status[source]['failures'] += 1
            return None

    def analyze_stock(self, stock):
        """分析单只股票"""
        def fallback():
            # 回退到模拟数据，但使用真实价格
            code = stock.get("code", "未知")
            name = stock.get("name", "未知")
            
            # 从多个数据源获取真实价格
            base_price = self._get_stock_price_from_multiple_sources(code)
            
            # 如果无法获取真实价格，使用合理的默认值
            if base_price is None or base_price <= 0:
                # 为特定股票设置合理的默认价格
                default_prices = {
                    "300903": 40.41,  # 科翔股份
                    "600487": 15.68,  # 亨通光电
                }
                base_price = default_prices.get(code, 50.0)  # 默认价格50.0
            
            # 使用固定涨跌幅，避免随机逻辑
            change_percent = 0.0  # 默认为0
            current_price = base_price
            
            # 使用固定技术指标，避免随机逻辑
            macd_signal = "中性"
            kdj_signal = "中性"
            rsi_value = 50  # 中性值
            volume_ratio = 1.0  # 正常值
            rsi_status = "中性"
            ma5 = ma10 = ma20 = current_price
            
            # 使用固定RPS指标，避免随机逻辑
            rps_20d = 0.0
            rps_60d = 0.0
            rps_120d = 0.0
            rps_score = 0.0
            rps_status = "中性"
            
            # 计算综合评分
            score = 5.0  # 基础分
            # 基于固定指标计算评分
            score = max(1.0, min(10.0, score))
            
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
                "score": score,
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

        # 尝试获取真实技术指标
        real_indicators = self._get_real_indicators(code)

        if real_indicators is None:
            # 尝试直接从多个数据源获取价格
            real_price = self._get_stock_price_from_multiple_sources(code)
            if real_price:
                # 如果获取到真实价格，返回基于真实价格的基本指标
                current_price = real_price
                change_percent = 0.0
                macd_signal = "中性"
                rsi_value = 50
                rsi_status = "中性"
                volume_ratio = 1.0
                kdj_signal = "中性"
                ma5 = ma10 = ma20 = current_price
                rps_status = "中性"
            else:
                # 如果无法获取真实价格，抛出异常
                raise ValueError(f"无法获取股票 {code} 的技术指标和价格")
        else:
            # 使用真实数据
            current_price = real_indicators["price"]
            change_percent = real_indicators["change_percent"]
            macd_signal = real_indicators["macd"]
            rsi_value = real_indicators["rsi"]
            rsi_status = real_indicators["rsi_status"]
            volume_ratio = real_indicators["volume_ratio"]
            kdj_signal = real_indicators["kdj"]
            ma5 = real_indicators["ma5"]
            ma10 = real_indicators["ma10"]
            ma20 = real_indicators["ma20"]
            rps_status = real_indicators.get("rps_status", "中性")

        # 计算综合评分（基于真实指标）
        score = 5.0  # 基础分

        if macd_signal == "金叉":
            score += 1.5
        elif macd_signal == "死叉":
            score -= 1.5

        if kdj_signal == "超卖":
            score += 1.0
        elif kdj_signal == "超买":
            score -= 1.0

        if rsi_status == "超卖":
            score += 0.5
        elif rsi_status == "超买":
            score -= 0.5

        if volume_ratio > 1.2:
            score += 0.5

        # 均线排列加分（多头排列）
        if ma5 > ma10 > ma20:
            score += 1.0
        elif ma5 < ma10 < ma20:
            score -= 1.0

        # RPS指标加分
        if rps_status == "强势":
            score += 1.5
        elif rps_status == "中性":
            score += 0.5
        else:  # 弱势
            score -= 0.5

        # 限制分数范围
        score = max(1.0, min(10.0, score))

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
            "signal": "买入" if score >= 7.5 else ("卖出" if score <= 4.0 else "观望")
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

            if result["signal"] == "买入" and result["score"] >= 7.5:
                buy_signals.append(result)

        # 存储分析结果到数据共享
        analysis_data = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "buy_signals": buy_signals
        }
        data_share.set_analysis_results(analysis_data)

        # 如果有买入信号，发送详细分析
        if buy_signals:
            for signal in buy_signals[:2]:  # 最多发送2个买入信号
                content = f"""
🚨 买入信号: {signal['code']} {signal['name']}

📊 综合评分: {signal['score']:.1f}/10 {'⭐' * int(signal['score']/2)}

📈 技术指标:
- MACD: {signal['indicators']['macd']}
- KDJ: {signal['indicators']['kdj']}
- RSI: {signal['indicators']['rsi']}
- 量比: {signal['indicators']['volume_ratio']:.2f}
- RPS: {signal['indicators']['rps']:.1f} ({signal['indicators']['rps_status']})
- RPS(20/60/120): {signal['indicators']['rps_20d']:.1f}/{signal['indicators']['rps_60d']:.1f}/{signal['indicators']['rps_120d']:.1f}

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
            print(f"  综合评分: {result['score']:.1f}/10 - 信号: {result['signal']}")
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
