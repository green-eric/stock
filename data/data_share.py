#!/usr/bin/env python3
"""
数据共享模块
负责在各个Agent之间共享数据
"""

import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable

class DataShare:
    """数据共享类"""
    
    def __init__(self, data_dir: str = "data", auto_save_interval: int = 30):
        """
        初始化数据共享
        
        Args:
            data_dir: 数据存储目录
            auto_save_interval: 自动保存间隔（秒）
        """
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.data: Dict[str, Any] = {}
        self.lock = threading.RLock()
        self.callbacks: Dict[str, List[Callable]] = {}
        self.last_save_time = datetime.now()
        self.auto_save_interval = auto_save_interval
        self._load_data()
        # 启动自动保存线程
        self._start_auto_save()
    
    def _start_auto_save(self):
        """启动自动保存线程"""
        def auto_save():
            while True:
                time.sleep(self.auto_save_interval)
                self._save_data()
        
        import time
        save_thread = threading.Thread(target=auto_save, daemon=True)
        save_thread.start()
    
    def _load_data(self):
        """加载数据"""
        try:
            data_file = os.path.join(self.data_dir, "shared_data.json")
            if os.path.exists(data_file):
                with open(data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
        except Exception as e:
            print(f"加载共享数据失败: {e}")
    
    def _save_data(self):
        """保存数据"""
        try:
            data_file = os.path.join(self.data_dir, "shared_data.json")
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            self.last_save_time = datetime.now()
        except Exception as e:
            print(f"保存共享数据失败: {e}")
    
    def set(self, key: str, value: Any, notify: bool = True):
        """
        设置数据
        
        Args:
            key: 数据键
            value: 数据值
            notify: 是否通知回调函数
        """
        with self.lock:
            try:
                # 验证键名
                if not isinstance(key, str) or not key:
                    print("数据键必须是非空字符串")
                    return
                
                old_value = self.data.get(key)
                self.data[key] = value
                # 检查是否需要立即保存
                if (datetime.now() - self.last_save_time).total_seconds() > self.auto_save_interval:
                    self._save_data()
                # 通知回调
                if notify and key in self.callbacks:
                    for callback in self.callbacks[key]:
                        try:
                            callback(value, old_value)
                        except Exception as e:
                            print(f"回调函数执行失败: {e}")
            except Exception as e:
                print(f"设置数据失败: {e}")
    
    def get(self, key: str, default: Any = None, max_age: Optional[int] = None) -> Any:
        """
        获取数据
        
        Args:
            key: 数据键
            default: 默认值
            max_age: 最大数据年龄（秒），超过则返回默认值
            
        Returns:
            数据值，如果不存在或过期返回默认值
        """
        with self.lock:
            value = self.data.get(key, default)
            if max_age and isinstance(value, dict) and 'timestamp' in value:
                try:
                    timestamp = datetime.fromisoformat(value['timestamp'])
                    if (datetime.now() - timestamp).total_seconds() > max_age:
                        return default
                except Exception:
                    pass
            return value
    
    def update(self, data: Dict[str, Any], notify: bool = True):
        """
        更新数据
        
        Args:
            data: 数据字典
            notify: 是否通知回调函数
        """
        with self.lock:
            for key, value in data.items():
                old_value = self.data.get(key)
                self.data[key] = value
                # 通知回调
                if notify and key in self.callbacks:
                    for callback in self.callbacks[key]:
                        try:
                            callback(value, old_value)
                        except Exception as e:
                            print(f"回调函数执行失败: {e}")
            # 检查是否需要立即保存
            if (datetime.now() - self.last_save_time).total_seconds() > self.auto_save_interval:
                self._save_data()
    
    def delete(self, key: str, notify: bool = True):
        """
        删除数据
        
        Args:
            key: 数据键
            notify: 是否通知回调函数
        """
        with self.lock:
            if key in self.data:
                old_value = self.data[key]
                del self.data[key]
                self._save_data()
                # 通知回调
                if notify and key in self.callbacks:
                    for callback in self.callbacks[key]:
                        try:
                            callback(None, old_value)
                        except Exception as e:
                            print(f"回调函数执行失败: {e}")
    
    def clear(self):
        """
        清空数据
        """
        with self.lock:
            self.data.clear()
            self._save_data()
    
    def get_all(self) -> Dict[str, Any]:
        """
        获取所有数据
        
        Returns:
            所有数据字典
        """
        with self.lock:
            return self.data.copy()
    
    def subscribe(self, key: str, callback: Callable):
        """
        订阅数据变更
        
        Args:
            key: 数据键
            callback: 回调函数，接收新值和旧值
        """
        with self.lock:
            if key not in self.callbacks:
                self.callbacks[key] = []
            self.callbacks[key].append(callback)
    
    def unsubscribe(self, key: str, callback: Callable):
        """
        取消订阅
        
        Args:
            key: 数据键
            callback: 回调函数
        """
        with self.lock:
            if key in self.callbacks:
                try:
                    self.callbacks[key].remove(callback)
                except ValueError:
                    pass
    
    # 特定数据操作方法
    def set_market_data(self, data: Dict[str, Any]):
        """
        设置市场数据
        
        Args:
            data: 市场数据
        """
        self.set("market_data", {
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_market_data(self, max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        获取市场数据
        
        Args:
            max_age: 最大数据年龄（秒），超过则返回None
            
        Returns:
            市场数据
        """
        market_data = self.get("market_data", max_age=max_age)
        if market_data:
            return market_data.get("data")
        return None
    
    def set_positions(self, positions: Dict[str, Any]):
        """
        设置持仓数据
        
        Args:
            positions: 持仓数据
        """
        self.set("positions", {
            "data": positions,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_positions(self, max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        获取持仓数据
        
        Args:
            max_age: 最大数据年龄（秒），超过则返回None
            
        Returns:
            持仓数据
        """
        positions = self.get("positions", max_age=max_age)
        if positions:
            return positions.get("data")
        return None
    
    def set_analysis_results(self, results: Dict[str, Any]):
        """
        设置分析结果
        
        Args:
            results: 分析结果
        """
        self.set("analysis_results", {
            "data": results,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_analysis_results(self, max_age: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        获取分析结果
        
        Args:
            max_age: 最大数据年龄（秒），超过则返回None
            
        Returns:
            分析结果
        """
        results = self.get("analysis_results", max_age=max_age)
        if results:
            return results.get("data")
        return None

# 创建全局数据共享实例
data_share = DataShare()
