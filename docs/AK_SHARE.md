# 多数据源集成指南

本文档介绍如何将 AKShare、新浪财经和东方财富等财经数据集成到数据采集Agent中，以获取实时市场数据。

## 概述

数据采集Agent (`agents/data_agent.py`) 现已支持通过多个数据源获取实时市场数据，包括：

- **AKShare**：综合财经数据接口
- **新浪财经**：实时行情数据
- **东方财富**：资金流向数据

支持的数据类型：
- **热点板块**：涨幅前5的板块及其领涨股
- **资金流向**：北向资金、主力资金、散户资金净流入
- **智能切换**：当主数据源失败时自动切换到备用数据源

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

### 数据源选择

默认情况下，Agent会使用AKShare作为主数据源。可以通过参数指定其他数据源：

```python
from agents.data_agent import DataCollectorAgent

# 使用默认数据源（AKShare）
agent = DataCollectorAgent()

# 指定新浪财经作为主数据源
agent = DataCollectorAgent(primary_source='sina')

# 指定东方财富作为主数据源
agent = DataCollectorAgent(primary_source='eastmoney')

# 强制使用模拟数据
agent = DataCollectorAgent(use_real_data=False)
```

### 智能切换机制

Agent内置智能数据源切换机制：
1. 首先尝试从主数据源获取数据
2. 如果主数据源失败，自动尝试其他可用的数据源
3. 如果所有数据源都失败，回退到模拟数据
4. 记录数据源状态，优先使用历史表现较好的数据源

### 环境变量配置

可以在环境变量中设置默认行为：

```bash
export DATA_AGENT_USE_REAL_DATA=true  # Linux/macOS
export DATA_AGENT_PRIMARY_SOURCE=akshare  # 可选: akshare, sina, eastmoney

set DATA_AGENT_USE_REAL_DATA=true     # Windows
set DATA_AGENT_PRIMARY_SOURCE=akshare  # 可选: akshare, sina, eastmoney
```

## 数据源说明

### AKShare 数据源
- **类型**: 综合财经数据接口
- **热点板块**: `ak.stock_sector_spot()`
- **资金流向**: `ak.stock_hsgt_fund_flow_summary_em()` 和 `ak.stock_market_fund_flow()`
- **特点**: 数据全面，接口丰富

### 新浪财经 数据源
- **类型**: 实时行情数据
- **热点板块**: 基于 `ak.stock_sector_spot()`（新浪财经数据）
- **资金流向**: 基于 `ak.stock_market_fund_flow()`（新浪财经数据）
- **特点**: 实时性好，更新速度快

### 东方财富 数据源
- **类型**: 资金流向数据
- **热点板块**: 基于 `ak.stock_sector_spot()`（东方财富数据）
- **资金流向**: 基于 `ak.stock_hsgt_fund_flow_summary_em()` 和 `ak.stock_market_fund_flow()`（东方财富数据）
- **特点**: 资金数据详细，分析工具丰富

### 数据处理逻辑
1. **热点板块**
   - 按涨跌幅排序，取前5个板块
   - 提取领涨股信息
   - 处理涨跌幅数据格式

2. **资金流向**
   - 北向资金: 从沪深港通数据中提取
   - 主力资金: 从市场资金流向数据中提取
   - 散户资金: 从小单净流入数据中提取
   - 单位转换: 元 → 亿（除以 100,000,000）

## 错误处理与降级机制

Agent内置多层错误处理和智能切换机制：

1. **导入级降级**: 如果AKShare无法导入，自动使用模拟数据
2. **API级降级**: 如果主数据源API调用失败，尝试其他数据源
3. **数据源级降级**: 如果所有数据源都失败，回退到模拟数据
4. **数据级降级**: 如果返回数据为空，使用模拟数据
5. **智能切换**: 记录数据源状态，优先使用历史表现较好的数据源

日志输出示例：
```
[DataAgent] akshare可用，将使用真实数据源
[DataAgent] 配置为使用真实市场数据，主数据源: AKShare
[DataAgent] 从AKShare获取数据失败: Connection timeout
[DataAgent] 尝试从备用数据源 新浪财经 获取数据
[DataAgent] 从新浪财经获取数据成功
[DataAgent] 数据源 新浪财经 失败，回退到模拟数据
[DataAgent] 尝试从备用数据源 东方财富 获取数据
[DataAgent] 从东方财富获取数据成功
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

### 多数据源测试
测试不同数据源的获取情况：

```python
from agents.data_agent import DataCollectorAgent

# 测试AKShare数据源
print("=== 测试AKShare数据源 ===")
agent_akshare = DataCollectorAgent(primary_source='akshare')
data_akshare = agent_akshare.collect_market_data()
print(f"数据源: {data_akshare.get('data_source')}")
print(f"热点板块: {len(data_akshare['hot_sectors'])}个")
print(f"北向资金: {data_akshare['capital_flow']['northbound_in']}亿")

# 测试新浪财经数据源
print("\n=== 测试新浪财经数据源 ===")
agent_sina = DataCollectorAgent(primary_source='sina')
data_sina = agent_sina.collect_market_data()
print(f"数据源: {data_sina.get('data_source')}")
print(f"热点板块: {len(data_sina['hot_sectors'])}个")
print(f"主力资金: {data_sina['capital_flow']['main_net_in']}亿")

# 测试东方财富数据源
print("\n=== 测试东方财富数据源 ===")
agent_eastmoney = DataCollectorAgent(primary_source='eastmoney')
data_eastmoney = agent_eastmoney.collect_market_data()
print(f"数据源: {data_eastmoney.get('data_source')}")
print(f"热点板块: {len(data_eastmoney['hot_sectors'])}个")
print(f"北向资金: {data_eastmoney['capital_flow']['northbound_in']}亿")
```

### 智能切换测试
测试数据源失败时的智能切换：

```python
from agents.data_agent import DataCollectorAgent

# 模拟数据源失败的情况
print("=== 测试智能切换 ===")
# 这里可以通过修改代码模拟数据源失败，或者在网络不稳定的环境下测试
agent = DataCollectorAgent(primary_source='akshare')
data = agent.collect_market_data()
print(f"最终使用的数据源: {data.get('data_source')}")
print(f"热点板块: {len(data['hot_sectors'])}个")
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
3. 数据源API变更
4. 数据源服务器暂时不可用

**解决方案**:
1. 检查当前时间是否在交易时段内
2. 测试网络连接: `python -c "import akshare; print(ak.stock_sector_spot().shape)"`
3. 查看相关数据源的最新文档
4. 系统会自动切换到其他可用数据源

### Q3: 数据单位不正确
**问题**: 资金流向数据显示异常大或小的数值。
**解决方案**: 检查单位转换逻辑，确保正确除以100,000,000（1亿）。

### Q4: 领涨股信息缺失
**问题**: 板块数据中没有领涨股信息。
**解决方案**: Agent会自动使用"未知"作为占位符，不影响整体功能。

### Q5: 数据源切换频繁
**问题**: 系统频繁在不同数据源之间切换。
**解决方案**:
1. 检查网络连接稳定性
2. 考虑增加数据源重试次数
3. 调整数据源优先级

## 扩展其他数据源

系统已内置支持多个数据源，可根据需要扩展：

### 现有数据源
- **AKShare**: 综合财经数据接口
- **新浪财经**: 实时行情数据
- **东方财富**: 资金流向数据

### 添加新数据源

1. **定义数据源配置**
   ```python
   # 在DATA_SOURCES字典中添加新数据源
   DATA_SOURCES = {
       'new_source': {
           'name': '新数据源名称',
           'available': True
       }
   }
   ```

2. **实现数据获取方法**
   ```python
   def _get_new_source_market_data(self, current_time):
       """从新数据源获取市场数据"""
       try:
           # 实现数据获取逻辑
           # 返回与其他数据源相同格式的数据
           return {
               "timestamp": current_time,
               "hot_sectors": [],
               "capital_flow": {},
               "data_source": "new_source"
           }
       except Exception as e:
           print(f"[DataAgent] 新数据源数据获取失败: {e}")
           return None
   ```

3. **更新数据源选择逻辑**
   ```python
   def _get_data_from_source(self, source, current_time):
       # 添加新数据源的处理逻辑
       if source == 'new_source':
           data = error_handler.try_execute_with_fallback(
               self._get_new_source_market_data,
               fallback,
               current_time
           )
   ```

### 添加新数据指标
1. 在相应的数据源方法中添加新的指标获取逻辑
2. 更新数据结构以包含新指标
3. 更新钉钉消息模板以显示新指标
4. 在数据共享模块中添加对新指标的支持

## 版本兼容性

### AKShare版本
| AKShare版本 | 支持状态 | 备注 |
|------------|----------|------|
| 1.18.x     | ✅ 完全支持 | 当前测试版本 |
| 1.17.x     | ✅ 支持 | 大部分函数兼容 |
| 1.16.x     | ⚠️ 部分支持 | 某些函数可能变更 |
| <1.16      | ❌ 不支持 | API差异较大 |

### 数据源兼容性
| 数据源 | 支持状态 | 依赖 |
|--------|----------|------|
| AKShare | ✅ 完全支持 | akshare, pandas |
| 新浪财经 | ✅ 完全支持 | akshare (内置接口) |
| 东方财富 | ✅ 完全支持 | akshare (内置接口) |

## 相关资源

1. [AKShare官方文档](https://akshare.akfamily.xyz/)
2. [AKShare GitHub](https://github.com/akfamily/akshare)
3. [新浪财经API文档](https://finance.sina.com.cn/)
4. [东方财富API文档](https://data.eastmoney.com/)
5. [项目架构文档](ARCH.md)
6. [用户手册](MANUAL.md)

## 更新日志

### v1.1 (2026-03-13)
- 添加多数据源支持（AKShare、新浪财经、东方财富）
- 实现智能数据源切换机制
- 优化错误处理和降级策略
- 更新文档和测试用例

### v1.0 (2026-03-08)
- 初始版本
- AKShare数据源集成
- 基础错误处理

---

**最后更新**: 2026-03-13
**维护者**: Data Agent 开发团队
**状态**: ✅ 生产就绪