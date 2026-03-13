#!/usr/bin/env python3
"""
数据存储模块
负责Redis和PostgreSQL的集成
"""

import json
import redis
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timedelta

class DataStorage:
    def __init__(self, redis_config=None, postgres_config=None):
        # Redis配置
        self.redis_config = redis_config or {
            "host": "localhost",
            "port": 6379,
            "db": 0
        }
        
        # PostgreSQL配置
        self.postgres_config = postgres_config or {
            "host": "localhost",
            "port": 5432,
            "database": "stock_system",
            "user": "postgres",
            "password": "postgres"
        }
        
        self.redis_client = None
        self.postgres_conn = None
        self.postgres_cursor = None
        
        # 初始化连接
        self._init_redis()
        self._init_postgres()
        
        # 初始化数据库表
        self._init_tables()
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(**self.redis_config)
            # 测试连接
            self.redis_client.ping()
            print("Redis连接成功")
        except Exception as e:
            print(f"Redis连接失败: {e}")
            self.redis_client = None
    
    def _init_postgres(self):
        """初始化PostgreSQL连接"""
        try:
            self.postgres_conn = psycopg2.connect(**self.postgres_config)
            self.postgres_cursor = self.postgres_conn.cursor(cursor_factory=DictCursor)
            print("PostgreSQL连接成功")
        except Exception as e:
            print(f"PostgreSQL连接失败: {e}")
            self.postgres_conn = None
            self.postgres_cursor = None
    
    def _init_tables(self):
        """初始化数据库表"""
        if not self.postgres_cursor:
            return
        
        try:
            # 创建市场数据表
            self.postgres_cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    change DECIMAL(10, 2) NOT NULL,
                    change_percent DECIMAL(10, 2) NOT NULL,
                    volume BIGINT NOT NULL,
                    amount DECIMAL(15, 2) NOT NULL,
                    open DECIMAL(10, 2) NOT NULL,
                    high DECIMAL(10, 2) NOT NULL,
                    low DECIMAL(10, 2) NOT NULL,
                    close DECIMAL(10, 2) NOT NULL,
                    prev_close DECIMAL(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建技术分析结果表
            self.postgres_cursor.execute('''
                CREATE TABLE IF NOT EXISTS technical_analysis (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    indicators JSONB NOT NULL,
                    score DECIMAL(5, 2) NOT NULL,
                    signal VARCHAR(10) NOT NULL,
                    suggestions JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建交易记录表
            self.postgres_cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    trade_id VARCHAR(30) NOT NULL UNIQUE,
                    order_id VARCHAR(30) NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    name VARCHAR(50) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    quantity INTEGER NOT NULL,
                    amount DECIMAL(15, 2) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    strategy VARCHAR(50) NOT NULL,
                    signal_id VARCHAR(30),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建风险评估表
            self.postgres_cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_assessments (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    market_risk JSONB NOT NULL,
                    position_risk JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建策略优化表
            self.postgres_cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_optimizations (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    strategy_name VARCHAR(50) NOT NULL,
                    parameters JSONB NOT NULL,
                    performance JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.postgres_conn.commit()
            print("数据库表初始化成功")
        except Exception as e:
            print(f"数据库表初始化失败: {e}")
            self.postgres_conn.rollback()
    
    def save_market_data(self, data):
        """保存市场数据到Redis和PostgreSQL"""
        try:
            # 保存到Redis（实时数据，1小时过期）
            if self.redis_client:
                key = f"market:{data['symbol']}"
                self.redis_client.setex(key, 3600, json.dumps(data))
            
            # 保存到PostgreSQL（历史数据）
            if self.postgres_cursor:
                self.postgres_cursor.execute('''
                    INSERT INTO market_data 
                    (timestamp, symbol, name, price, change, change_percent, volume, amount, open, high, low, close, prev_close)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    datetime.fromisoformat(data['timestamp']),
                    data['symbol'],
                    data['name'],
                    data['price'],
                    data['change'],
                    data['change_percent'],
                    data['volume'],
                    data['amount'],
                    data['open'],
                    data['high'],
                    data['low'],
                    data['close'],
                    data['prev_close']
                ))
                self.postgres_conn.commit()
            
            return True
        except Exception as e:
            print(f"保存市场数据失败: {e}")
            if self.postgres_conn:
                self.postgres_conn.rollback()
            return False
    
    def save_technical_analysis(self, data):
        """保存技术分析结果到PostgreSQL"""
        try:
            if self.postgres_cursor:
                self.postgres_cursor.execute('''
                    INSERT INTO technical_analysis 
                    (timestamp, symbol, name, indicators, score, signal, suggestions)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    datetime.fromisoformat(data['timestamp']),
                    data['symbol'],
                    data['name'],
                    json.dumps(data['indicators']),
                    data['score'],
                    data['signal'],
                    json.dumps(data.get('suggestions', {}))
                ))
                self.postgres_conn.commit()
            
            return True
        except Exception as e:
            print(f"保存技术分析结果失败: {e}")
            if self.postgres_conn:
                self.postgres_conn.rollback()
            return False
    
    def save_trade(self, data):
        """保存交易记录到PostgreSQL"""
        try:
            if self.postgres_cursor:
                self.postgres_cursor.execute('''
                    INSERT INTO trades 
                    (trade_id, order_id, symbol, name, side, price, quantity, amount, timestamp, strategy, signal_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    data['trade_id'],
                    data['order_id'],
                    data['symbol'],
                    data['name'],
                    data['side'],
                    data['price'],
                    data['quantity'],
                    data['amount'],
                    datetime.fromisoformat(data['timestamp']),
                    data['strategy'],
                    data.get('signal_id', '')
                ))
                self.postgres_conn.commit()
            
            return True
        except Exception as e:
            print(f"保存交易记录失败: {e}")
            if self.postgres_conn:
                self.postgres_conn.rollback()
            return False
    
    def save_risk_assessment(self, data):
        """保存风险评估结果到PostgreSQL"""
        try:
            if self.postgres_cursor:
                self.postgres_cursor.execute('''
                    INSERT INTO risk_assessments 
                    (timestamp, market_risk, position_risk)
                    VALUES (%s, %s, %s)
                ''', (
                    datetime.fromisoformat(data['timestamp']),
                    json.dumps(data['market_risk']),
                    json.dumps(data['position_risk'])
                ))
                self.postgres_conn.commit()
            
            return True
        except Exception as e:
            print(f"保存风险评估失败: {e}")
            if self.postgres_conn:
                self.postgres_conn.rollback()
            return False
    
    def save_strategy_optimization(self, data):
        """保存策略优化结果到PostgreSQL"""
        try:
            if self.postgres_cursor:
                self.postgres_cursor.execute('''
                    INSERT INTO strategy_optimizations 
                    (timestamp, strategy_name, parameters, performance)
                    VALUES (%s, %s, %s, %s)
                ''', (
                    datetime.fromisoformat(data['timestamp']),
                    data['strategy_name'],
                    json.dumps(data['parameters']),
                    json.dumps(data['performance'])
                ))
                self.postgres_conn.commit()
            
            return True
        except Exception as e:
            print(f"保存策略优化结果失败: {e}")
            if self.postgres_conn:
                self.postgres_conn.rollback()
            return False
    
    def get_market_data(self, symbol, use_cache=True):
        """获取市场数据"""
        try:
            # 优先从Redis获取实时数据
            if use_cache and self.redis_client:
                key = f"market:{symbol}"
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            
            # 从PostgreSQL获取最新数据
            if self.postgres_cursor:
                self.postgres_cursor.execute('''
                    SELECT * FROM market_data 
                    WHERE symbol = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', (symbol,))
                row = self.postgres_cursor.fetchone()
                if row:
                    return dict(row)
            
            return None
        except Exception as e:
            print(f"获取市场数据失败: {e}")
            return None
    
    def get_technical_analysis(self, symbol, limit=10):
        """获取技术分析结果"""
        try:
            if self.postgres_cursor:
                self.postgres_cursor.execute('''
                    SELECT * FROM technical_analysis 
                    WHERE symbol = %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                ''', (symbol, limit))
                rows = self.postgres_cursor.fetchall()
                return [dict(row) for row in rows]
            return []
        except Exception as e:
            print(f"获取技术分析结果失败: {e}")
            return []
    
    def get_all_technical_analysis(self, limit=10):
        """获取所有股票的技术分析结果"""
        try:
            if self.postgres_cursor:
                self.postgres_cursor.execute('''
                    SELECT * FROM technical_analysis 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                ''', (limit,))
                rows = self.postgres_cursor.fetchall()
                return [dict(row) for row in rows]
            return []
        except Exception as e:
            print(f"获取所有技术分析结果失败: {e}")
            return []
    
    def get_trades(self, symbol=None, limit=100):
        """获取交易记录"""
        try:
            if self.postgres_cursor:
                if symbol:
                    self.postgres_cursor.execute('''
                        SELECT * FROM trades 
                        WHERE symbol = %s 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    ''', (symbol, limit))
                else:
                    self.postgres_cursor.execute('''
                        SELECT * FROM trades 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    ''', (limit,))
                rows = self.postgres_cursor.fetchall()
                return [dict(row) for row in rows]
            return []
        except Exception as e:
            print(f"获取交易记录失败: {e}")
            return []
    
    def get_risk_assessments(self, limit=10):
        """获取风险评估记录"""
        try:
            if self.postgres_cursor:
                self.postgres_cursor.execute('''
                    SELECT * FROM risk_assessments 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                ''', (limit,))
                rows = self.postgres_cursor.fetchall()
                return [dict(row) for row in rows]
            return []
        except Exception as e:
            print(f"获取风险评估记录失败: {e}")
            return []
    
    def get_strategy_optimizations(self, strategy_name=None, limit=10):
        """获取策略优化记录"""
        try:
            if self.postgres_cursor:
                if strategy_name:
                    self.postgres_cursor.execute('''
                        SELECT * FROM strategy_optimizations 
                        WHERE strategy_name = %s 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    ''', (strategy_name, limit))
                else:
                    self.postgres_cursor.execute('''
                        SELECT * FROM strategy_optimizations 
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    ''', (limit,))
                rows = self.postgres_cursor.fetchall()
                return [dict(row) for row in rows]
            return []
        except Exception as e:
            print(f"获取策略优化记录失败: {e}")
            return []
    
    def close(self):
        """关闭连接"""
        try:
            if self.redis_client:
                self.redis_client.close()
            if self.postgres_cursor:
                self.postgres_cursor.close()
            if self.postgres_conn:
                self.postgres_conn.close()
            print("连接已关闭")
        except Exception as e:
            print(f"关闭连接失败: {e}")

if __name__ == "__main__":
    # 测试数据存储模块
    storage = DataStorage()
    
    # 测试保存市场数据
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
    
    print("测试保存市场数据:")
    result = storage.save_market_data(test_market_data)
    print(f"保存结果: {result}")
    
    # 测试获取市场数据
    print("\n测试获取市场数据:")
    data = storage.get_market_data("002594")
    print(f"获取结果: {data}")
    
    # 测试保存技术分析结果
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
    
    print("\n测试保存技术分析结果:")
    result = storage.save_technical_analysis(test_analysis_data)
    print(f"保存结果: {result}")
    
    # 测试获取技术分析结果
    print("\n测试获取技术分析结果:")
    analysis = storage.get_technical_analysis("002594")
    print(f"获取结果: {analysis}")
    
    # 关闭连接
    storage.close()