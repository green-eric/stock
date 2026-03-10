# 🤖 多Agent炒股系统

## 📋 项目概述

**多Agent炒股系统**是一个专为**散户超短线（1-3天）**操作设计的智能投资辅助系统。系统通过多个协同工作的Agent，结合钉钉实时推送，提供市场热点追踪、技术分析、买卖信号和风险控制等功能。

### 📊 实施状态

**当前版本**: v1.0.2 (AKShare真实数据版)
**最后更新**: 2026-03-10
**系统状态**: ✅ 核心功能已实现，运行稳定

#### 🎯 已实现功能
| 模块 | 状态 | 说明 |
|------|------|------|
| **数据采集Agent** | ✅ 运行中 | AKShare真实热点板块、资金流向数据（智能降级机制），5分钟间隔（仅交易时段） |
| **技术分析Agent** | ✅ 运行中 | 基于配置文件监控列表的模拟技术分析，15分钟间隔（仅交易时段） |
| **风险控制Agent** | ✅ 运行中 | 监控市场风险和持仓风险，执行止损操作 |
| **交易执行Agent** | ✅ 运行中 | 执行买卖操作，管理交易订单 |
| **策略优化Agent** | ✅ 运行中 | 基于历史数据优化交易策略 |
| **系统监控Agent** | ✅ 运行中 | 实时监控Agent状态，30分钟间隔（全天运行） |
| **钉钉集成** | ✅ 正常 | 签名校验、消息推送、速率限制 |
| **数据存储** | ✅ 正常 | Redis实时数据，PostgreSQL历史数据 |
| **API接口** | ✅ 正常 | FastAPI接口，支持系统管理和数据查询 |

#### ⚠️ 注意事项
1. **混合数据源**: 数据采集Agent使用AKShare真实数据（智能降级机制），技术分析Agent使用模拟分析（可配置监控列表）
2. **交易时段限制**: 数据采集和技术分析仅在09:00-15:00运行
3. **无实盘交易**: 仅信号推送，不执行实际买卖操作
4. **简化指标**: 技术分析基于模拟MACD/KDJ/RSI/成交量指标，可从配置文件扩展监控股票

### 🎯 核心特性

- **🤖 多Agent协同**: 数据采集、技术分析、风险控制、交易执行、策略优化、系统监控六大Agent协同工作
- **📱 钉钉集成**: 实时消息推送，支持签名校验和关键词过滤
- **⚡ 超短线优化**: 专为1-3天持股周期设计的热点追踪策略
- **🔐 风险控制**: 完整的仓位管理、止损机制和熔断保护
- **🔄 自动化运行**: 定时任务，7×24小时不间断监控
- **📊 数据存储**: Redis实时数据，PostgreSQL历史数据
- **🌐 API接口**: FastAPI接口，支持系统管理和数据查询
- **📈 监控系统**: Prometheus + Grafana监控，ELK Stack日志管理

### 🚀 快速开始

```bash
# 1. 检查系统配置
./start_agents.sh status

# 2. 启动所有Agent
./start_agents.sh start

# 3. 查看系统状态
./start_agents.sh status

# 4. 停止系统
./start_agents.sh stop
```

---

## 📁 项目结构

```
./
├── 📂 agents/                    # Agent核心代码
│   ├── data_agent.py             # 数据采集Agent
│   ├── technical_agent.py        # 技术分析Agent
│   ├── risk_agent.py             # 风险控制Agent
│   ├── trade_agent.py            # 交易执行Agent
│   ├── strategy_agent.py         # 策略优化Agent
│   ├── monitor_agent.py          # 系统监控Agent
│   └── dingtalk_integration.md   # 钉钉集成架构设计
├── 📂 api/                       # API接口
│   └── main.py                   # API主文件
├── 📂 config/                    # 配置文件
│   ├── data_collector.json       # 数据采集配置
│   ├── monitor_config.json       # 监控配置
│   ├── risk_controller.json      # 风险控制配置
│   ├── strategy_analyzer.json    # 策略分析配置
│   ├── system.json               # 系统配置
│   └── watch_list.txt            # 监控股票列表
├── 📂 data/                      # 数据存储
│   └── storage.py                # 数据存储模块
├── 📂 docs/                      # 文档
│   ├── AKSHARE_INTEGRATION.md    # AKShare集成文档
│   ├── ARCHITECTURE.md           # 架构文档
│   ├── COMPLETE_SOLUTION.md      # 完整解决方案
│   ├── MAINTENANCE_GUIDE.md      # 维护指南
│   ├── REDESIGNED_ARCHITECTURE.md # 重新设计的架构
│   ├── TEST_PLAN.md              # 测试计划
│   ├── USER_GUIDE.md             # 用户指南
│   └── USER_MANUAL.md            # 用户手册
├── 📂 tests/                     # 测试用例
│   ├── test_agents.py            # Agent测试
│   └── test_storage.py           # 存储测试
├── 📜 .gitignore                 # Git忽略文件
├── 📜 Dockerfile.agent           # Agent服务Dockerfile
├── 📜 Dockerfile.api             # API服务Dockerfile
├── 📜 README.md                  # 本文档
├── 📜 REDESIGNED_ARCHITECTURE.md  # 架构文档
├── 📜 SYSTEM_DOCUMENTATION.md    # 系统文档
├── 📜 TECHNICAL_DOCUMENT.md      # 技术文档
├── 📜 dingtalk_sender.py         # 钉钉消息发送器
├── 📜 docker-compose.yml         # Docker Compose配置
├── 📜 list_akshare_funcs.py      # AKShare函数列表
├── 📜 prometheus.yml             # Prometheus配置
├── 📜 requirements.txt           # 依赖包
└── 📜 start_agents.sh            # 系统启动脚本
```

---

## 🏗️ 系统架构

### 架构图

```
┌─────────────────────────────────────────────────────────┐
│                   接入层                                 │
│  • 钉钉机器人Webhook                                   │
│  • Web管理界面                                         │
│  • API接口                                             │
└───────────────┬─────────────────────────────────────────┘
                │
┌─────────────────────────────────────────────────────────┐
│                   服务层                                 │
│  • 消息处理服务                                         │
│  • API网关服务                                         │
│  • 认证授权服务                                         │
└───────────────┬─────────────────────────────────────────┘
                │
┌─────────────────────────────────────────────────────────┐
│                   Agent层                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ 数据采集    │  │ 技术分析    │  │ 风险控制    │      │
│  │ Agent       │  │ Agent       │  │ Agent       │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │ 交易执行    │  │ 系统监控    │  │ 策略优化    │      │
│  │ Agent       │  │ Agent       │  │ Agent       │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└───────────────┬─────────────────────────────────────────┘
                │
┌─────────────────────────────────────────────────────────┐
│                   数据层                                 │
│  • 实时数据 (Redis)                                     │
│  • 历史数据 (PostgreSQL)                                │
│  • 配置数据 (PostgreSQL)                                │
│  • 日志数据 (Elasticsearch)                             │
└─────────────────────────────────────────────────────────┘
```

### Agent职责

#### 1. 数据采集Agent (Data Collector)
- **运行频率**: 每5分钟
- **功能**:
  - 收集市场热点板块数据
  - 监控资金流向变化
  - 跟踪新闻舆情
- **输出**: 市场数据 + 钉钉热点推送

#### 2. 技术分析Agent (Technical Analyst)
- **运行频率**: 每15分钟
- **功能**:
  - 多指标技术分析 (MACD/KDJ/RSI/成交量)
  - 买卖信号生成
  - 风险预警
- **输出**: 分析结果 + 钉钉买卖信号

#### 3. 风险控制Agent (Risk Controller)
- **运行频率**: 每10分钟
- **功能**:
  - 监控市场风险
  - 监控持仓风险
  - 执行止损操作
  - 风险报告生成
- **输出**: 风险评估 + 止损信号

#### 4. 交易执行Agent (Trade Executor)
- **运行频率**: 每5分钟
- **功能**:
  - 执行买卖操作
  - 管理交易订单
  - 处理交易回调
  - 交易记录存储
- **输出**: 交易记录 + 订单状态

#### 5. 策略优化Agent (Strategy Optimizer)
- **运行频率**: 每1小时
- **功能**:
  - 基于历史数据优化交易策略
  - 评估策略性能
  - 生成策略建议
  - 策略参数调优
- **输出**: 策略建议 + 优化结果

#### 6. 系统监控Agent (System Monitor)
- **运行频率**: 每30分钟
- **功能**:
  - 监控各Agent健康状态
  - 检查系统资源使用
  - 发送状态报告
- **输出**: 状态报告 + 钉钉健康报告

---

## 🔧 钉钉集成

### 配置信息

```json
{
  "webhook": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
  "secret": "SECxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "enable": true,
  "settings": {
    "enable_alerts": true,
    "alert_types": ["买入信号", "卖出信号", "止损提醒", "热点推送", "异动预警", "系统状态"],
    "quiet_hours": [],
    "rate_limit": 18,
    "user_mode": "散户超短线",
    "holding_period": "1-3天"
  }
}
```

### 消息类型

| 类型 | 图标 | 触发条件 | 紧急程度 |
|------|------|---------|---------|
| **买入信号** | 🚨 | 综合评分≥7.5，技术面+资金面共振 | 紧急 |
| **卖出信号** | 🔴 | 跌破止损或出现利空 | 紧急 |
| **止损提醒** | ⚠️ | 价格接近止损位 | 高 |
| **热点推送** | 🔔 | 板块涨幅>3%或资金大幅流入 | 普通 |
| **异动预警** | 📈 | 个股异常波动 | 高 |
| **系统状态** | 🤖 | 定时状态报告 | 普通 |

### 安全特性

1. **签名校验**: 防止消息伪造
2. **关键词过滤**: 必须包含预设关键词
3. **速率限制**: ≤18条/分钟
4. **静默时段**: 可配置免打扰时间

---

## 📱 使用指南

### 钉钉指令集

#### 查询指令
```
"热点" / "今天有什么热点？"      → 推送今日热点板块
"分析 002594" / "帮我分析002594" → 生成五位一体分析
"持仓" / "当前持仓怎么样？"      → 推送持仓盈亏报告
"状态" / "系统状态如何？"        → 推送Agent健康状态
"帮助"                          → 查看完整指令列表
```

#### 操作指令
```
"买入 002594 10%"               → 买入10%仓位
"卖出 002594 全部"              → 卖出全部持仓
"止损 002594 200"               → 设置止损价200元
"目标 002594 240"               → 设置目标价240元
```

#### 配置指令
```
"模式 激进"                     → 设置风险模式为激进
"关注 AI 新能源"                → 只关注AI和新能源板块
"限额 3%"                       → 设置单日最大亏损3%
```

### 日常操作流程

```
08:30-09:15 数据Agent准备开盘数据
09:15       钉钉推送开盘热点
09:30-11:30 技术分析Agent实时扫描 (每15分钟)
            钉钉推送买卖信号 (实时)
11:30       钉钉推送午间复盘
13:00-15:00 继续实时监控
15:00       钉钉推送收盘总结
15:00-16:00 监控Agent绩效分析
```

---

## ⚙️ 配置管理

### 风险控制参数

```json
{
  "risk_control": {
    "max_position_per_stock": 0.3,      // 单只股票最大仓位30%
    "daily_loss_limit": 0.05,           // 单日最大亏损5%
    "max_consecutive_losses": 3,        // 连续止损3次
    "cooling_period_hours": 24,         // 冷却时间24小时
    "stop_loss_percent": 0.08,          // 止损比例8%
    "take_profit_percent": 0.1          // 止盈比例10%
  }
}
```

### 用户偏好设置

```json
{
  "user_preferences": {
    "risk_level": "high",               // 风险等级：高
    "holding_period": "1-3天",          // 持仓周期：1-3天
    "preferred_sectors": [              // 关注板块
      "AI人工智能",
      "新能源车",
      "半导体",
      "金融科技",
      "消费电子"
    ]
  }
}
```

### Agent运行参数

```json
{
  "agent_settings": {
    "data_collector": {
      "enabled": true,
      "interval_seconds": 300,          // 5分钟
      "sources": ["market_data", "news", "capital_flow"]
    },
    "technical_analysis": {
      "enabled": true,
      "interval_seconds": 900,          // 15分钟
      "indicators": ["MACD", "KDJ", "RSI", "VOLUME", "BOLL"]
    },
    "signal_fusion": {
      "enabled": true,
      "weights": {
        "technical": 0.4,               // 技术面权重40%
        "capital": 0.3,                 // 资金面权重30%
        "fundamental": 0.2,             // 基本面权重20%
        "news": 0.1                     // 消息面权重10%
      },
      "buy_threshold": 7.5,             // 买入阈值7.5分
      "sell_threshold": 4.0             // 卖出阈值4.0分
    }
  }
}
```

---

## 🚀 部署与运维

### 环境要求

- **Python**: 3.9+
- **Docker**: 20.04+
- **Docker Compose**: 1.29+
- **网络**: 稳定的互联网连接
- **存储**: 至少100MB可用空间

### 部署步骤

#### 1. 基础环境
```bash
# 克隆项目代码
git clone <your-git-repository-url>
cd MultiAgentStockSystem

# 设置权限
chmod +x ./start_agents.sh
```

#### 2. 钉钉配置
1. 在钉钉群创建自定义机器人
2. 设置机器人名称：`多Agent炒股助手`
3. 配置安全设置（关键词、签名等）
4. 获取Webhook地址和Secret
5. 更新`config/dingtalk.json`配置文件

#### 3. 系统启动
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 系统管理

#### 启动/停止
```bash
# 启动所有Agent
./start_agents.sh start

# 停止所有Agent
./start_agents.sh stop

# 重启系统
./start_agents.sh restart
```

#### 状态监控
```bash
# 查看Agent状态
./start_agents.sh status

# 查看实时日志
docker-compose logs -f

# 检查数据文件
ls -la ./data/
```

#### 故障排查
```bash
# 检查配置文件
cat ./config/dingtalk.json

# 检查容器状态
docker-compose ps
```

---

## 🔍 故障排除

### 常见问题

#### 1. 钉钉收不到消息
- **原因**: 关键词不匹配或签名错误
- **解决**:
  ```bash
  # 检查关键词设置
  # 消息必须包含钉钉机器人设置的关键词
  ```

#### 2. Agent停止运行
- **原因**: 容器崩溃或资源不足
- **解决**:
  ```bash
  # 查看日志
  docker-compose logs -f

  # 重启系统
  docker-compose restart
  ```

#### 3. 数据不更新
- **原因**: 数据采集Agent异常
- **解决**:
  ```bash
  # 检查数据Agent状态
  docker-compose logs data_agent

  # 手动测试数据采集
  docker exec -it stock_data_agent python -m agents.data_agent
  ```

### 日志分析

#### 数据采集日志
```bash
docker-compose logs data_agent
```
- 正常输出: `[时间] 收集市场数据...`
- 错误输出: `数据采集错误: [错误信息]`

#### 技术分析日志
```bash
docker-compose logs technical_agent
```
- 正常输出: `[时间] 分析股票...`
- 信号输出: `发现 [数量] 个买入信号`

#### 系统监控日志
```bash
docker-compose logs monitor_agent
```
- 正常输出: `[时间] 检查系统状态...`
- 状态输出: `状态报告发送成功/失败`

---

## 📈 性能指标

### 运行指标
- **启动时间**: <5秒
- **消息延迟**: <2秒 (网络正常时)
- **数据更新频率**: 5分钟
- **分析频率**: 15分钟
- **监控频率**: 30分钟

### 质量指标
- **系统可用性**: 99.9% (设计目标)
- **消息成功率**: >95% (网络正常时)
- **故障恢复**: <60秒
- **资源占用**: <100MB内存

### 业务指标
- **信号准确率**: 待回测验证
- **平均持仓周期**: 1-3天
- **胜率目标**: >60%
- **盈亏比目标**: >1.5

---

## 📚 技术文档

### API参考

#### 钉钉消息发送器
```python
from dingtalk_sender import DingTalkSender

# 初始化
sender = DingTalkSender(config_file="/path/to/config.json")

# 发送普通消息
sender.send_message(
    title="消息标题",
    content="消息内容",
    msg_type="markdown",  # text/markdown/actionCard
    level="info"          # info/warning/error/urgent
)

# 发送股票预警
sender.send_stock_alert(
    stock_code="002594",
    stock_name="比亚迪",
    alert_type="买入信号",  # 买入信号/卖出信号/止损提醒/异动预警
    price=225.0,
    change_percent=2.5,
    reason="技术面突破",
    suggestion="建议买入10%仓位"
)
```

#### API接口
- **健康检查**: `GET /api/v1/system/health`
- **系统状态**: `GET /api/v1/system/status`
- **市场数据**: `GET /api/v1/data/market`
- **技术分析**: `GET /api/v1/data/analysis`
- **交易记录**: `GET /api/v1/data/trades`
- **策略列表**: `GET /api/v1/strategies`
- **下单**: `POST /api/v1/trades/order`

### 开发指南

#### 添加新Agent
1. 在`agents/`目录创建新Agent文件
2. 实现Agent核心逻辑
3. 集成钉钉消息发送
4. 更新Docker Compose配置
5. 测试验证

#### 扩展数据源
1. 实现数据采集接口
2. 添加数据解析逻辑
3. 集成到数据采集Agent
4. 测试数据准确性

#### 自定义分析策略
1. 修改技术分析算法
2. 调整信号生成逻辑
3. 优化权重参数
4. 回测验证效果

---

## 👥 贡献指南

### 代码规范
- 使用Python 3.9+语法
- 遵循PEP 8编码规范
- 添加必要的注释和文档
- 编写单元测试

### 提交流程
1. Fork项目仓库
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request
5. 等待代码审查

### 测试要求
- 新功能必须包含测试用例
- 确保钉钉集成测试通过
- 验证Agent协同工作正常
- 检查性能影响

---

## 📄 许可证

本项目采用**专有许可证**，仅限授权用户使用。

### 使用限制
1. 禁止商业用途
2. 禁止代码分发
3. 禁止反向工程
4. 遵守相关法律法规

### 免责声明
本系统仅为投资辅助工具，不构成投资建议。股市有风险，投资需谨慎。用户应自行承担投资风险，系统开发者不对任何投资损失负责。

---

## 📞 支持与联系

### 问题反馈
- **GitHub Issues**: 提交技术问题
- **钉钉群**: 实时技术支持
- **邮件**: 联系项目维护者

### 文档资源
- [系统架构设计](REDESIGNED_ARCHITECTURE.md)
- [系统文档](SYSTEM_DOCUMENTATION.md)
- [技术文档](TECHNICAL_DOCUMENT.md)

### 更新日志
- **v1.0** (2026-03-08): 初始版本发布
  - 多Agent基础架构
  - 钉钉集成
  - 超短线策略
  - 风险控制系统

- **v1.0.2** (2026-03-10): 功能增强
  - 新增风险控制Agent
  - 新增交易执行Agent
  - 新增策略优化Agent
  - 新增API接口
  - 新增Docker部署支持

---

**最后更新**: 2026-03-10
**版本**: v1.0.2
**状态**: ✅ 生产就绪