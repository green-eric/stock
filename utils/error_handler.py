#!/usr/bin/env python3
"""
错误处理模块
负责统一处理系统错误
"""

import logging
import traceback
import time
from typing import Optional, Callable, Any, Dict, List, Tuple

class ErrorHandler:
    """错误处理类"""
    
    def __init__(self):
        """
        初始化错误处理器
        """
        self.logger = logging.getLogger(__name__)
        self.error_stats: Dict[str, int] = {}
        self.error_history: List[Tuple[str, str, float]] = []
        self.max_history = 1000
    
    def handle_error(self, error: Exception, context: str = "", fallback: Optional[Callable] = None) -> Any:
        """
        处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文
            fallback: 回退函数
            
        Returns:
            回退函数的返回值，如果没有回退函数返回None
        """
        error_type = type(error).__name__
        error_msg = f"{context} 错误: {str(error)}"
        
        # 记录错误统计
        self._record_error(error_type, context)
        
        # 记录错误日志
        self.logger.error(error_msg)
        self.logger.error(traceback.format_exc())
        
        if fallback:
            try:
                return fallback()
            except Exception as fallback_error:
                fallback_error_msg = f"回退函数执行失败: {str(fallback_error)}"
                self.logger.error(fallback_error_msg)
                self._record_error(type(fallback_error).__name__, f"回退函数: {context}")
        
        return None
    
    def try_execute(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """
        尝试执行函数，捕获并处理错误
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果，如果发生错误返回None
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = f"执行函数 {func.__name__} 时"
            return self.handle_error(e, context)
    
    def try_execute_with_fallback(self, func: Callable, fallback: Callable, *args, **kwargs) -> Any:
        """
        尝试执行函数，捕获并处理错误，失败时执行回退函数
        
        Args:
            func: 要执行的函数
            fallback: 回退函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果或回退函数的返回值
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = f"执行函数 {func.__name__} 时"
            return self.handle_error(e, context, fallback)
    
    def try_execute_with_retry(self, func: Callable, max_retries: int = 3, retry_delay: float = 1.0, *args, **kwargs) -> Optional[Any]:
        """
        尝试执行函数，失败时重试
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果，如果多次失败返回None
        """
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = f"执行函数 {func.__name__} 时 (尝试 {attempt + 1}/{max_retries})"
                if attempt < max_retries - 1:
                    self.logger.warning(f"{context} 失败: {str(e)}，将重试...")
                    time.sleep(retry_delay)
                else:
                    return self.handle_error(e, context)
        return None
    
    def _record_error(self, error_type: str, context: str):
        """
        记录错误信息
        
        Args:
            error_type: 错误类型
            context: 错误上下文
        """
        # 更新错误统计
        if error_type not in self.error_stats:
            self.error_stats[error_type] = 0
        self.error_stats[error_type] += 1
        
        # 添加到错误历史
        self.error_history.append((error_type, context, time.time()))
        # 限制历史记录数量
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
    
    def get_error_stats(self) -> Dict[str, int]:
        """
        获取错误统计
        
        Returns:
            错误类型到发生次数的映射
        """
        return self.error_stats.copy()
    
    def get_recent_errors(self, hours: int = 24) -> List[Tuple[str, str, float]]:
        """
        获取最近的错误
        
        Args:
            hours: 时间范围（小时）
            
        Returns:
            最近的错误列表
        """
        cutoff_time = time.time() - (hours * 3600)
        return [(error_type, context, timestamp) for error_type, context, timestamp in self.error_history if timestamp >= cutoff_time]
    
    def clear_error_stats(self):
        """
        清空错误统计
        """
        self.error_stats.clear()
        self.error_history.clear()

# 创建全局错误处理器实例
error_handler = ErrorHandler()
