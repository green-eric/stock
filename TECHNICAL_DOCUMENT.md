# 多Agent炒股系统技术文档

## 概述

多Agent炒股系统是一个专为散户超短线（1-3天）操作设计的智能投资辅助系统。系统通过多个协同工作的Agent，结合钉钉实时推送，提供市场热点追踪、技术分析、买卖信号和风险控制等功能。

**版本**: v1.1 (AKShare真实数据版)
**最后更新**: 2026-03-08
**系统状态**: ✅ 核心功能已实现，运行稳定

## 系统架构

### Agent架构
系统采用多Agent协同架构，包含三个核心Agent：

1. **数据采集Agent** (Data Collector)
   - 运行频率: 每5分钟（交易时段09:00-15:00）
   - 功能: 收集市场热点板块数据、监控资金流向变化、跟踪新闻舆情
   - 数据源: AKShare真实数据（智能降级机制）
   - 输出: 市场数据JSON文件 + 钉钉热点推送

2. **技术分析Agent** (Technical Analyst)
   - 运行频率: 每15分钟（交易时段09:00-15:00）
   - 功能: 多指标技术分析 (MACD/KDJ/RSI/成交量)、买卖信号生成、风险预警
   - 分析对象: 配置文件`config/watch_list.txt`中的股票列表
   - 输出: 分析结果JSON文件 + 钉钉买卖信号

3. **系统监控Agent** (System Monitor)
   - 运行频率: 每30分钟（全天运行）
   - 功能: 监控各Agent健康状态、检查系统资源使用、发送状态报告
   - 输出: 状态报告JSON文件 + 钉钉健康报告

### 数据流架构
```
钉钉控制中心 → Agent调度 → 数据采集 → 技术分析 → 信号推送
```

## 核心模块

### Agent模块
- **agents/data_agent.py**: 数据采集Agent主程序
- **agents/technical_agent.py**: 技术分析Agent主程序
- **agents/monitor_agent_simple.py**: 系统监控Agent主程序

### 钉钉集成模块
- **dingtalk_sender.py**: 钉钉消息发送器核心类
- **dingtalk_notifier.py**: 钉钉通知器
- **config/dingtalk.json**: 钉钉配置文件

### 配置管理模块
- **config/**: 包含所有Agent的配置文件
- **config/watch_list.txt**: 技术分析监控股票列表

### 数据存储模块
- **data/**: 存储市场数据、分析结果和系统状态JSON文件
- **logs/**: 存储各Agent的运行日志

## API参考

### DingTalkSender类
```python
from dingtalk_sender import DingTalkSender

# 初始化
sender = DingTalkSender(config_file="config/dingtalk.json")

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

### 数据采集Agent API
```python
# 运行数据采集Agent
python agents/data_agent.py

# 核心参数
# - use_real_data: 是否使用真实数据源（默认True）
# - interval_seconds: 采集间隔（默认300秒）
```

### 技术分析Agent API
```python
# 运行技术分析Agent
python agents/technical_agent.py

# 核心参数
# - watch_list: 监控股票列表（从config/watch_list.txt读取）
# - interval_seconds: 分析间隔（默认900秒）
```

## 配置文件说明

### dingtalk.json
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

### watch_list.txt
```
# 监控股票列表（每行一个股票代码）
002594  # 比亚迪
000858  # 五粮液
600519  # 贵州茅台
```

### Agent配置文件
- **data_collector.json**: 数据采集Agent配置
- **technical_analysis.json**: 技术分析Agent配置
- **monitor_config.json**: 系统监控Agent配置

## 部署指南

### 环境要求
- **Python**: 3.8+
- **依赖包**: akshare, requests, pandas
- **操作系统**: Linux (推荐Ubuntu/CentOS)
- **网络**: 稳定的互联网连接
- **存储**: 至少100MB可用空间

### 安装步骤
1. 克隆源码到本地
2. 安装Python依赖: `pip install akshare requests pandas`
3. 配置钉钉机器人: 获取webhook和secret
4. 更新配置文件: 修改`config/dingtalk.json`
5. 设置监控股票: 编辑`config/watch_list.txt`
6. 启动系统: `./start_agents.sh start`

### 系统管理
```bash
# 启动所有Agent
./start_agents.sh start

# 停止所有Agent
./start_agents.sh stop

# 查看系统状态
./start_agents.sh status

# 重启系统
./start_agents.sh restart
```

## 开发指南

### 添加新Agent
1. 在`agents/`目录创建新Agent文件
2. 实现Agent核心逻辑（继承基类或实现标准接口）
3. 集成钉钉消息发送功能
4. 更新启动脚本`start_agents.sh`
5. 添加配置文件到`config/`目录
6. 测试验证

### 扩展数据源
1. 实现数据采集接口
2. 添加数据解析逻辑
3. 集成到数据采集Agent
4. 测试数据准确性
5. 更新配置文件

### 自定义分析策略
1. 修改技术分析算法（`agents/technical_agent.py`）
2. 调整信号生成逻辑
3. 优化权重参数
4. 回测验证效果

## 性能指标

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

## 故障排除

### 常见问题
1. **钉钉收不到消息**
   - 检查关键词设置（消息必须包含钉钉机器人设置的关键词）
   - 验证签名是否正确
   - 检查网络连接

2. **Agent停止运行**
   - 查看日志文件: `logs/`目录
   - 检查进程状态: `ps aux | grep agent`
   - 重启系统: `./start_agents.sh restart`

3. **数据不更新**
   - 检查数据采集Agent状态
   - 验证AKShare数据源是否可用
   - 检查网络连接

### 日志分析
- **数据采集日志**: `logs/data_agent.log`
- **技术分析日志**: `logs/technical_agent.log`
- **系统监控日志**: `logs/monitor_agent_simple.log`

## 安全考虑

### 钉钉安全
1. **签名校验**: 防止消息伪造
2. **关键词过滤**: 必须包含预设关键词
3. **速率限制**: ≤18条/分钟
4. **静默时段**: 可配置免打扰时间

### 系统安全
1. **配置文件保护**: 敏感信息不提交到版本控制
2. **权限控制**: 最小权限原则运行Agent
3. **输入验证**: 所有外部输入都经过验证
4. **错误处理**: 完善的异常处理机制

## 扩展计划

### 短期扩展 (1-2周)
1. **真实数据源集成**: 接入更多数据源（新浪财经、东方财富）
2. **技术指标增强**: 添加布林带、均线系统
3. **用户体验优化**: 添加Web控制面板

### 中期扩展 (1-2月)
1. **多市场支持**: 港股、美股、加密货币市场
2. **智能算法**: 机器学习预测模型
3. **自动化交易**: 实盘交易接口

### 长期愿景 (3-6月)
1. **云端部署**: 高可用架构
2. **多用户支持**: 用户管理系统
3. **生态建设**: 策略市场、社区交流

## 相关文档

- [系统架构设计](docs/ARCHITECTURE.md)
- [AKShare集成指南](docs/AKSHARE_INTEGRATION.md)
- [用户手册](docs/USER_MANUAL.md)
- [维护指南](docs/MAINTENANCE_GUIDE.md)
- [README](README.md)

## 许可证

本项目采用**专有许可证**，仅限授权用户使用。

### 使用限制
1. 禁止商业用途
2. 禁止代码分发
3. 禁止反向工程
4. 遵守相关法律法规

### 免责声明
本系统仅为投资辅助工具，不构成投资建议。股市有风险，投资需谨慎。用户应自行承担投资风险，系统开发者不对任何投资损失负责。

---
*最后更新: 2026-03-08*
*版本: v1.1*
*状态: ✅ 生产就绪*