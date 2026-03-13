#!/usr/bin/env python3
"""
API接口主文件
使用FastAPI创建系统API接口
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import json
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入Agent和存储模块
from agents.data_agent import DataCollectorAgent
from agents.technical_agent import TechnicalAnalysisAgent
from agents.risk_agent import RiskControllerAgent
from agents.trade_agent import TradeExecutorAgent
from agents.strategy_agent import StrategyOptimizerAgent
from data.storage import DataStorage

# 创建FastAPI应用
app = FastAPI(
    title="多Agent炒股系统API",
    description="多Agent炒股系统的API接口",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化组件
storage = DataStorage()
data_agent = DataCollectorAgent(primary_source='tushare')
technical_agent = TechnicalAnalysisAgent()
risk_agent = RiskControllerAgent()
trade_agent = TradeExecutorAgent()
strategy_agent = StrategyOptimizerAgent()

# 数据模型
class Order(BaseModel):
    symbol: str
    name: str
    side: str
    price: float
    quantity: int
    strategy: str = "manual"
    signal_id: str = ""

class Strategy(BaseModel):
    name: str
    parameters: dict

class UserConfig(BaseModel):
    name: str
    email: str
    preferences: dict

# 系统管理接口
@app.get("/api/v1/system/status")
async def get_system_status():
    """获取系统状态"""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "data_agent": "active",
            "technical_agent": "active",
            "risk_agent": "active",
            "trade_agent": "active",
            "strategy_agent": "active"
        },
        "version": "1.0.0"
    }

@app.post("/api/v1/agents/{agent_id}/start")
async def start_agent(agent_id: str):
    """启动Agent"""
    # 模拟启动Agent
    return {
        "status": "success",
        "message": f"Agent {agent_id} started",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """停止Agent"""
    # 模拟停止Agent
    return {
        "status": "success",
        "message": f"Agent {agent_id} stopped",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """获取Agent状态"""
    return {
        "status": "active",
        "agent_id": agent_id,
        "timestamp": datetime.now().isoformat()
    }

# 数据管理接口
@app.get("/api/v1/data/market")
async def get_market_data(symbol: str = None):
    """获取市场数据"""
    if symbol:
        data = storage.get_market_data(symbol)
        if data:
            return data
        else:
            raise HTTPException(status_code=404, detail="Market data not found")
    else:
        # 使用数据采集模块获取市场数据，与钉钉显示格式保持一致
        data = data_agent.collect_market_data()
        return data

@app.get("/api/v1/data/analysis")
async def get_technical_analysis(symbol: str = None, limit: int = 10):
    """获取技术分析结果"""
    if symbol:
        analysis = storage.get_technical_analysis(symbol, limit)
        return {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "analysis": analysis
        }
    else:
        # 当没有提供symbol时，返回所有股票的技术分析结果，与钉钉消息格式一致
        results = []
        buy_signals = []
        
        for stock in technical_agent.watch_list:
            result = technical_agent.analyze_stock(stock)
            results.append(result)
            
            if result["signal"] == "买入" and result["score"] >= 7.5:
                buy_signals.append(result)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "buy_signals": buy_signals
        }

@app.get("/api/v1/data/analysis/all")
async def get_all_technical_analysis(limit: int = 10):
    """获取所有股票的技术分析结果"""
    results = []
    buy_signals = []
    
    for stock in technical_agent.watch_list:
        result = technical_agent.analyze_stock(stock)
        results.append(result)
        
        if result["signal"] == "买入" and result["score"] >= 7.5:
            buy_signals.append(result)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "buy_signals": buy_signals
    }

@app.get("/api/v1/data/trades")
async def get_trades(symbol: str = None, limit: int = 100):
    """获取交易记录"""
    trades = storage.get_trades(symbol, limit)
    return {
        "timestamp": datetime.now().isoformat(),
        "trades": trades
    }

# 策略管理接口
@app.get("/api/v1/strategies")
async def get_strategies():
    """获取策略列表"""
    return {
        "timestamp": datetime.now().isoformat(),
        "strategies": [
            {
                "name": "technical_analysis",
                "display_name": "技术分析策略",
                "description": "基于技术指标的交易策略"
            },
            {
                "name": "trend_following",
                "display_name": "趋势跟踪策略",
                "description": "跟随市场趋势的交易策略"
            },
            {
                "name": "mean_reversion",
                "display_name": "均值回归策略",
                "description": "基于均值回归的交易策略"
            }
        ]
    }

@app.post("/api/v1/strategies")
async def create_strategy(strategy: Strategy):
    """创建策略"""
    return {
        "status": "success",
        "message": f"Strategy {strategy.name} created",
        "timestamp": datetime.now().isoformat()
    }

@app.put("/api/v1/strategies/{strategy_id}")
async def update_strategy(strategy_id: str, strategy: Strategy):
    """更新策略"""
    return {
        "status": "success",
        "message": f"Strategy {strategy_id} updated",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/strategies/{strategy_id}/backtest")
async def backtest_strategy(strategy_id: str):
    """回测策略"""
    result = strategy_agent.backtest_strategy(strategy_id, {})
    return result

# 交易接口
@app.post("/api/v1/trades/order")
async def place_order(order: Order):
    """下单"""
    result = trade_agent.place_order({
        "symbol": order.symbol,
        "name": order.name,
        "side": order.side,
        "price": order.price,
        "quantity": order.quantity,
        "strategy": order.strategy,
        "signal_id": order.signal_id
    })
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/v1/trades/orders/{order_id}/cancel")
async def cancel_order(order_id: str):
    """撤单"""
    result = trade_agent.cancel_order(order_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/api/v1/trades/orders/{order_id}")
async def get_order_status(order_id: str):
    """获取订单状态"""
    result = trade_agent.get_order_status(order_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/v1/trades/positions")
async def get_positions():
    """获取当前持仓"""
    return trade_agent.get_positions()

# 用户接口
@app.post("/api/v1/auth/login")
async def login(username: str, password: str):
    """用户认证"""
    # 模拟认证
    return {
        "status": "success",
        "token": "mock_token",
        "user_id": "123456",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/users/{user_id}/config")
async def get_user_config(user_id: str):
    """获取用户配置"""
    return {
        "user_id": user_id,
        "config": {
            "name": "测试用户",
            "email": "test@example.com",
            "preferences": {
                "notification": True,
                "risk_level": "medium",
                "strategy": "technical_analysis"
            }
        },
        "timestamp": datetime.now().isoformat()
    }

@app.put("/api/v1/users/{user_id}/config")
async def update_user_config(user_id: str, config: UserConfig):
    """更新用户配置"""
    return {
        "status": "success",
        "message": f"User {user_id} config updated",
        "timestamp": datetime.now().isoformat()
    }

# 健康检查接口
@app.get("/api/v1/system/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "up",
            "storage": "up",
            "agents": "up"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)