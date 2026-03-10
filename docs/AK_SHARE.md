# AKShare 集成指南

本文档介绍如何将 AKShare 财经数据集成到数据采集Agent中，以获取实时市场数据。

## 概述

数据采集Agent (`agents/data_agent.py`) 现已支持通过 AKShare 库获取实时市场数据，包括：

- **热点板块**：涨幅前5的板块及其领涨股
- **资金流向**：北向资金、主力资金、散户资金净流入

## 安装依赖

### 前提条件
- Python 3.7+
- pip 包管理器

### 安装 AKShare

```bash
# 方法1: 使用系统pip安装
pip install akshare pandas

# 方法2: 在项目虚拟环境中安装
python -m venv venv
venv\Scripts\activate  # Windows
pip install akshare pandas

# 方法3: 使用特定版本（推荐）
pip install akshare==1.18.35 pandas==3.0.1
```

### 验证安装

```bash
python -c "import akshare; print(akshare.__version__)"
```

## 配置使用

### 启用真实数据

默认情况下，Agent会尝试使用AKShare获取真实数据。如果AKShare不可用，将自动回退到模拟数据。

```python
from agents.data_agent import DataCollectorAgent

# 使用真实数据（默认）
agent = DataCollectorAgent(use_real_data=True)

# 强制使用模拟数据
agent = DataCollectorAgent(use_real_data=False)
```

### 环境变量配置

可以在环境变量中设置默认行为：

```bash
export DATA_AGENT_USE_REAL_DATA=true  # Linux/macOS
set DATA_AGENT_USE_REAL_DATA=true     # Windows
```

## 数据源说明

### 热点板块数据
- **源函数**: `ak.stock_sector_spot()`
- **数据列**: 板块名称、涨跌幅、领涨股代码、领涨股名称
- **处理逻辑**: 按涨跌幅排序，取前5个板块

### 资金流向数据
1. **北向资金** (沪深港通)
   - **源函数**: `ak.stock_hsgt_fund_flow_summary_em()`
   - **筛选**: 资金方向为"北向"的记录
   - **单位转换**: 元 → 亿（除以 100,000,000）

2. **主力资金 & 散户资金**
   - **源函数**: `ak.stock_market_fund_flow()`
   - **数据列**: 主力净流入-净额、小单净流入-净额
   - **单位转换**: 元 → 亿（除以 100,000,000）

## 错误处理与降级机制

Agent内置多层错误处理：

1. **导入级降级**: 如果AKShare无法导入，自动使用模拟数据
2. **API级降级**: 如果AKShare API调用失败，回退到模拟数据
3. **数据级降级**: 如果返回数据为空，使用模拟数据

日志输出示例：
```
[DataAgent] akshare可用，将使用真实数据源
[DataAgent] 配置为使用真实市场数据
[DataAgent] 获取热点板块失败: Connection timeout
[DataAgent] 回退到模拟数据
```

## 交易时段控制

Agent仅在交易时段（9:00-15:00）主动收集数据，避免非交易时段调用无效API。

```python
# 在 run() 方法中控制
if 9 <= datetime.now().hour < 15:
    self.send_market_summary()
```

## 性能优化

### 缓存机制
考虑实现简单缓存，避免频繁调用API：

```python
# 示例缓存实现（未来版本）
self.cache = {}
self.cache_ttl = 300  # 5分钟

def get_cached_data(self, key, fetch_func):
    if key in self.cache and time.time() - self.cache[key]['timestamp'] < self.cache_ttl:
        return self.cache[key]['data']
    data = fetch_func()
    self.cache[key] = {'data': data, 'timestamp': time.time()}
    return data
```

### 并发限制
避免高频调用AKShare API，建议间隔至少5分钟。

## 测试验证

### 单元测试
运行现有测试套件：

```bash
python test_data_agent_unit.py
```

### 集成测试
测试真实数据获取：

```bash
python test_data_agent_integration.py
```

### 手动验证
```python
from agents.data_agent import DataCollectorAgent
agent = DataCollectorAgent()
data = agent.collect_market_data()
print(f"热点板块: {len(data['hot_sectors'])}个")
print(f"北向资金: {data['capital_flow']['northbound_in']}亿")
```

## 常见问题

### Q1: AKShare安装失败
**问题**: 安装时出现依赖冲突或编译错误。
**解决方案**:
1. 使用较新版本的pip: `pip install --upgrade pip`
2. 使用conda环境: `conda install -c conda-forge akshare`
3. 安装预编译版本: `pip install akshare --no-deps` (不推荐)

### Q2: 数据返回为空
**可能原因**:
1. 非交易时段（9:30-15:00）
2. 网络连接问题
3. AKShare API变更

**解决方案**:
1. 检查当前时间是否在交易时段内
2. 测试网络连接: `python -c "import akshare; print(ak.stock_sector_spot().shape)"`
3. 查看AKShare最新文档

### Q3: 数据单位不正确
**问题**: 资金流向数据显示异常大或小的数值。
**解决方案**: 检查单位转换逻辑，确保正确除以100,000,000（1亿）。

### Q4: 领涨股信息缺失
**问题**: 板块数据中没有领涨股信息。
**解决方案**: Agent会自动使用"未知"作为占位符，不影响整体功能。

## 扩展其他数据源

AKShare支持多种数据源，可根据需要扩展：

### 备用数据源配置
```python
# 示例：多数据源选择
DATA_SOURCES = {
    'akshare': {
        'sector': ak.stock_sector_spot,
        'flow': ak.stock_market_fund_flow,
    },
    'sina': {
        # 新浪财经接口
    },
    'eastmoney': {
        # 东方财富接口
    }
}
```

### 添加新数据指标
1. 在`_get_capital_flow()`方法中添加新的资金流向指标
2. 在`_get_hot_sectors()`方法中调整板块筛选逻辑
3. 更新钉钉消息模板以显示新指标

## 版本兼容性

| AKShare版本 | 支持状态 | 备注 |
|------------|----------|------|
| 1.18.x     | ✅ 完全支持 | 当前测试版本 |
| 1.17.x     | ✅ 支持 | 大部分函数兼容 |
| 1.16.x     | ⚠️ 部分支持 | 某些函数可能变更 |
| <1.16      | ❌ 不支持 | API差异较大 |

## 相关资源

1. [AKShare官方文档](https://akshare.akfamily.xyz/)
2. [AKShare GitHub](https://github.com/akfamily/akshare)
3. [项目架构文档](ARCHITECTURE.md)
4. [用户手册](USER_MANUAL.md)

---

**最后更新**: 2026-03-08
**维护者**: Data Agent 开发团队
**状态**: ✅ 生产就绪