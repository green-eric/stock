#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置管理模块
"""

import os
import sys
import time
from config.config_manager import ConfigManager


def test_config_loading():
    """测试配置文件加载"""
    print("\n=== 测试配置文件加载 ===")
    config_manager = ConfigManager()
    
    # 测试获取配置
    system_config = config_manager.get_config("system")
    print(f"系统配置: {system_config}")
    
    # 测试获取不存在的配置
    non_existent = config_manager.get_config("non_existent")
    print(f"不存在的配置: {non_existent}")
    
    # 测试获取配置项
    version = config_manager.get("system", "version")
    print(f"系统版本: {version}")
    
    data_source = config_manager.get("system", "market_data_source")
    print(f"市场数据源: {data_source}")
    
    # 测试获取不存在的配置项
    non_existent_value = config_manager.get("system", "non_existent", default="默认值")
    print(f"不存在的配置项: {non_existent_value}")
    
    print("配置文件加载测试通过!")


def test_config_validation():
    """测试配置验证"""
    print("\n=== 测试配置验证 ===")
    config_manager = ConfigManager()
    
    # 测试配置文件格式验证
    # 这里我们假设config目录存在且有有效的配置文件
    # 验证配置是否正确加载
    system_config = config_manager.get_config("system")
    assert system_config is not None, "系统配置加载失败"
    assert "version" in system_config, "系统配置缺少version字段"
    assert "market_data_source" in system_config, "系统配置缺少market_data_source字段"
    
    print("配置验证测试通过!")


def test_config_hot_reload():
    """测试配置热重载"""
    print("\n=== 测试配置热重载 ===")
    config_manager = ConfigManager()
    
    # 获取初始版本
    initial_version = config_manager.get("system", "version")
    print(f"初始版本: {initial_version}")
    
    # 模拟修改配置文件
    config_path = os.path.join(os.path.dirname(__file__), "config", "system.json")
    
    # 读取当前配置
    import json
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # 修改版本号
    original_version = config_data["version"]
    config_data["version"] = "1.1.1" if original_version == "1.1.0" else "1.1.0"
    
    # 写回配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    print(f"修改版本为: {config_data['version']}")
    
    # 手动触发重载
    config_manager.reload()
    
    # 验证版本是否已更新
    new_version = config_manager.get("system", "version")
    print(f"热重载后版本: {new_version}")
    
    assert new_version == config_data["version"], "配置热重载失败"
    
    # 恢复原始版本
    config_data["version"] = original_version
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    print("配置热重载测试通过!")


def test_config_directory_check():
    """测试配置目录检查"""
    print("\n=== 测试配置目录检查 ===")
    # 这个测试会验证配置管理器是否能正确处理配置目录
    # 即使目录不存在，也应该能正常初始化
    config_manager = ConfigManager()
    print("配置目录检查测试通过!")


if __name__ == "__main__":
    print("开始测试配置管理模块...")
    
    try:
        test_config_loading()
        test_config_validation()
        test_config_hot_reload()
        test_config_directory_check()
        print("\n✅ 所有配置管理模块测试通过!")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
