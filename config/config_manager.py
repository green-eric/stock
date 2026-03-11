#!/usr/bin/env python3
"""
配置管理模块
负责统一管理系统配置
"""

import json
import os
import threading
import time
from typing import Dict, Any, Optional, List, Callable

class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config_dir: str = "config", auto_reload_interval: int = 300):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
            auto_reload_interval: 自动重新加载间隔（秒）
        """
        self.config_dir = config_dir
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.lock = threading.RLock()
        self.auto_reload_interval = auto_reload_interval
        self._load_all_configs()
        # 启动自动重新加载线程
        self._start_auto_reload()
    
    def _start_auto_reload(self):
        """启动自动重新加载线程"""
        def auto_reload():
            while True:
                time.sleep(self.auto_reload_interval)
                self.reload()
        
        reload_thread = threading.Thread(target=auto_reload, daemon=True)
        reload_thread.start()
    
    def _load_all_configs(self):
        """加载所有配置文件"""
        try:
            if not os.path.exists(self.config_dir):
                print(f"配置目录不存在: {self.config_dir}")
                return
                
            config_files = os.listdir(self.config_dir)
            for file_name in config_files:
                if file_name.endswith('.json'):
                    config_name = file_name.replace('.json', '')
                    config_path = os.path.join(self.config_dir, file_name)
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            new_config = json.load(f)
                            # 验证配置格式
                            if not isinstance(new_config, dict):
                                print(f"配置文件 {file_name} 格式错误: 必须是字典格式")
                                continue
                            
                            # 检查配置是否有变化
                            old_config = self.configs.get(config_name)
                            self.configs[config_name] = new_config
                            # 通知回调
                            if old_config != new_config and config_name in self.callbacks:
                                for callback in self.callbacks[config_name]:
                                    try:
                                        callback(new_config, old_config)
                                    except Exception as e:
                                        print(f"配置回调函数执行失败: {e}")
                    except json.JSONDecodeError as e:
                        print(f"配置文件 {file_name} 解析失败: {e}")
                    except Exception as e:
                        print(f"加载配置文件 {file_name} 失败: {e}")
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    
    def get_config(self, config_name: str) -> Optional[Dict[str, Any]]:
        """
        获取配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            配置字典，如果配置不存在返回None
        """
        with self.lock:
            return self.configs.get(config_name)
    
    def get(self, config_name: str, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            config_name: 配置名称
            key: 配置键
            default: 默认值
            
        Returns:
            配置值，如果不存在返回默认值
        """
        with self.lock:
            config = self.get_config(config_name)
            if config:
                return config.get(key, default)
            return default
    
    def update_config(self, config_name: str, config: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            config_name: 配置名称
            config: 配置字典
            
        Returns:
            是否更新成功
        """
        with self.lock:
            try:
                config_path = os.path.join(self.config_dir, f"{config_name}.json")
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                old_config = self.configs.get(config_name)
                self.configs[config_name] = config
                # 通知回调
                if old_config != config and config_name in self.callbacks:
                    for callback in self.callbacks[config_name]:
                        try:
                            callback(config, old_config)
                        except Exception as e:
                            print(f"配置回调函数执行失败: {e}")
                return True
            except Exception as e:
                print(f"更新配置文件失败: {e}")
                return False
    
    def reload(self):
        """重新加载所有配置"""
        with self.lock:
            self._load_all_configs()
    
    def subscribe(self, config_name: str, callback: Callable):
        """
        订阅配置变更
        
        Args:
            config_name: 配置名称
            callback: 回调函数，接收新配置和旧配置
        """
        with self.lock:
            if config_name not in self.callbacks:
                self.callbacks[config_name] = []
            self.callbacks[config_name].append(callback)
    
    def unsubscribe(self, config_name: str, callback: Callable):
        """
        取消订阅
        
        Args:
            config_name: 配置名称
            callback: 回调函数
        """
        with self.lock:
            if config_name in self.callbacks:
                try:
                    self.callbacks[config_name].remove(callback)
                except ValueError:
                    pass
    
    def get_system_config(self) -> Dict[str, Any]:
        """
        获取系统配置
        
        Returns:
            系统配置字典
        """
        with self.lock:
            return self.get_config("system") or {}
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        获取Agent配置
        
        Args:
            agent_name: Agent名称
            
        Returns:
            Agent配置字典
        """
        with self.lock:
            return self.get_config(agent_name) or {}

# 创建全局配置管理器实例
config_manager = ConfigManager()
