import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入被测试的模块
from build_notify import BuildConfig, BuildNotifier, format_svn_log, get_svn_logs

class TestBuildNotify(unittest.TestCase):
    def setUp(self):
        """测试前的设置"""
        self.config = BuildConfig()
        
    def test_build_config_initialization(self):
        """测试BuildConfig类的初始化"""
        self.assertEqual(self.config.token, "YOUR_TOKEN_HERE")
        self.assertEqual(self.config.endpoint, "https://models.inference.ai.azure.com")
        self.assertEqual(self.config.model_name, "gpt-4o")

    def test_format_svn_log(self):
        """测试SVN日志格式化功能"""
        test_log = """
r123 | user1 | 2023-12-20 10:00:00 +0800
Changed paths:
   M /trunk/src/file1.cpp
   A /trunk/src/file2.cpp
   D /trunk/src/file3.cpp

修复了一个bug，添加了新功能

r124 | user2 | 2023-12-21 11:00:00 +0800
Changed paths:
   M /trunk/src/file4.cpp

优化性能
"""
        expected_output = [
            {
                "revision": "123",
                "author": "user1",
                "date": "2023-12-20 10:00:00 +0800",
                "changed_paths": [
                    {"action": "M", "path": "/trunk/src/file1.cpp"},
                    {"action": "A", "path": "/trunk/src/file2.cpp"},
                    {"action": "D", "path": "/trunk/src/file3.cpp"}
                ],
                "message": "修复了一个bug，添加了新功能"
            },
            {
                "revision": "124",
                "author": "user2",
                "date": "2023-12-21 11:00:00 +0800",
                "changed_paths": [
                    {"action": "M", "path": "/trunk/src/file4.cpp"}
                ],
                "message": "优化性能"
            }
        ]
        
        result = format_svn_log(test_log)
        self.assertEqual(result, expected_output)

    @patch('subprocess.check_output')
    def test_get_svn_logs_success(self, mock_check_output):
        """测试成功获取SVN日志"""
        # 模拟subprocess.check_output的返回值
        mock_check_output.return_value = """
r123 | user1 | 2023-12-20 10:00:00 +0800
Changed paths:
   M /trunk/src/file1.cpp

修复bug
""".encode('utf-8')
        
        result = get_svn_logs("http://svn.example.com/repo", "123", "124")
        
        # 验证subprocess.check_output被正确调用
        mock_check_output.assert_called_once()
        
        # 验证返回结果
        expected = [
            {
                "revision": "123",
                "author": "user1",
                "date": "2023-12-20 10:00:00 +0800",
                "changed_paths": [
                    {"action": "M", "path": "/trunk/src/file1.cpp"}
                ],
                "message": "修复bug"
            }
        ]
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main() 