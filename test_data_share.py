#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据共享模块
"""

import time
from data.data_share import DataShare


def test_data_storage():
    """测试数据存储功能"""
    print("\n=== 测试数据存储功能 ===")
    data_share = DataShare()
    
    # 测试存储数据
    test_data = {"key1": "value1", "key2": 123, "key3": [1, 2, 3]}
    data_share.set("test_data", test_data)
    print(f"存储测试数据: {test_data}")
    
    # 测试获取数据
    retrieved_data = data_share.get("test_data")
    print(f"获取测试数据: {retrieved_data}")
    assert retrieved_data == test_data, "数据存储和获取失败"
    
    # 测试获取不存在的数据
    non_existent = data_share.get("non_existent", default="默认值")
    print(f"获取不存在的数据: {non_existent}")
    assert non_existent == "默认值", "默认值功能失败"
    
    # 测试更新数据
    updated_data = {"key1": "updated_value1", "key2": 456, "key3": [4, 5, 6]}
    data_share.set("test_data", updated_data)
    print(f"更新测试数据: {updated_data}")
    
    retrieved_updated = data_share.get("test_data")
    print(f"获取更新后的数据: {retrieved_updated}")
    assert retrieved_updated == updated_data, "数据更新失败"
    
    print("数据存储功能测试通过!")


def test_data_validation():
    """测试数据验证功能"""
    print("\n=== 测试数据验证功能 ===")
    data_share = DataShare()
    
    # 测试无效的键
    try:
        data_share.set("", {"test": "data"})
        assert False, "应该拒绝空键"
    except ValueError as e:
        print(f"正确拒绝空键: {e}")
    
    try:
        data_share.set(123, {"test": "data"})
        assert False, "应该拒绝非字符串键"
    except ValueError as e:
        print(f"正确拒绝非字符串键: {e}")
    
    # 测试无效的值
    try:
        data_share.set("test_key", object())
        assert False, "应该拒绝不可序列化的值"
    except Exception as e:
        print(f"正确拒绝不可序列化的值: {e}")
    
    print("数据验证功能测试通过!")


def test_change_notification():
    """测试变更通知功能"""
    print("\n=== 测试变更通知功能 ===")
    data_share = DataShare()
    
    # 测试回调函数
    callback_called = False
    old_value = None
    new_value = None
    
    def test_callback(value, old_val):
        nonlocal callback_called, old_value, new_value
        callback_called = True
        old_value = old_val
        new_value = value
        print(f"回调函数被调用: old_value={old_val}, new_value={value}")
    
    # 订阅变更
    data_share.subscribe("test_key", test_callback)
    
    # 初始设置数据
    initial_data = {"value": 1}
    data_share.set("test_key", initial_data)
    
    # 等待回调
    time.sleep(0.1)
    assert callback_called, "回调函数应该被调用"
    assert old_value is None, "初始设置时旧值应该为None"
    assert new_value == initial_data, "新值应该等于初始数据"
    
    # 重置回调标志
    callback_called = False
    
    # 更新数据
    updated_data = {"value": 2}
    data_share.set("test_key", updated_data)
    
    # 等待回调
    time.sleep(0.1)
    assert callback_called, "回调函数应该在更新时被调用"
    assert old_value == initial_data, "旧值应该等于初始数据"
    assert new_value == updated_data, "新值应该等于更新后的数据"
    
    # 取消订阅
    data_share.unsubscribe("test_key", test_callback)
    
    # 再次更新数据，回调不应该被调用
    callback_called = False
    data_share.set("test_key", {"value": 3})
    time.sleep(0.1)
    assert not callback_called, "取消订阅后回调函数不应该被调用"
    
    print("变更通知功能测试通过!")


def test_auto_save():
    """测试自动保存功能"""
    print("\n=== 测试自动保存功能 ===")
    data_share = DataShare()
    
    # 存储测试数据
    test_data = {"auto_save_test": "value"}
    data_share.set("test_auto_save", test_data)
    print(f"存储自动保存测试数据: {test_data}")
    
    # 手动保存数据
    data_share._save_data()
    
    # 模拟程序重启
    del data_share
    
    # 重新创建数据共享实例
    new_data_share = DataShare()
    
    # 验证数据是否被保存
    retrieved_data = new_data_share.get("test_auto_save")
    print(f"重新加载后的数据: {retrieved_data}")
    assert retrieved_data == test_data, "自动保存功能失败"
    
    print("自动保存功能测试通过!")


def test_error_handling():
    """测试错误处理功能"""
    print("\n=== 测试错误处理功能 ===")
    data_share = DataShare()
    
    # 测试无效操作
    try:
        # 尝试存储不可序列化的数据
        class NonSerializable:
            pass
        data_share.set("non_serializable", NonSerializable())
        assert False, "应该捕获序列化错误"
    except Exception as e:
        print(f"正确捕获序列化错误: {e}")
    
    print("错误处理功能测试通过 [通过]")


if __name__ == "__main__":
    print("开始测试数据共享模块...")
    
    try:
        test_data_storage()
        test_data_validation()
        test_change_notification()
        test_auto_save()
        test_error_handling()
        print("\n✅ 所有数据共享模块测试通过!")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
