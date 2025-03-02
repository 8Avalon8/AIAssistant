import os
from mem0 import Memory

class MemoryClient:
    def __init__(self):
        self.config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "code_review",
                    "host": "107.175.75.21:6333/",
                    "port": 6333,
                    "embedding_model_dims": 768,
                },
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "gemini-2.0-flash-exp",
                    "temperature": 0.2,
                    "max_tokens": 8000,
                    "api_key": os.environ["OPENAI_API_KEY"],
                    "openai_base_url": os.environ["OPENAI_API_BASE"],
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-004",
                },
            },
        }
        self.memory = Memory.from_config(self.config)

    def add_memory(self, content, user_id, output_format="text"):
        """
        添加代码审查记录到记忆库
        
        Args:
            content (str): 代码审查内容
            user_id (str): SVN提交者ID
            output_format (str): 输出格式，默认为text
        """
        try:
            self.memory.add(content, user_id=user_id, metadata={"format": output_format})
            return True, "记忆添加成功"
        except Exception as e:
            return False, f"记忆添加失败: {str(e)}"

    def get_memories(self, user_id, limit=10):
        """
        获取指定用户的代码审查历史记录
        
        Args:
            user_id (str): SVN提交者ID
            limit (int): 返回记录数量限制
        
        Returns:
            list: 历史记录列表
        """
        try:
            memories = self.memory.get_all(
                user_id=user_id,
                limit=limit
            )
            return True, memories
        except Exception as e:
            return False, f"获取记忆失败: {str(e)}"

    def search_memories(self, query, user_id=None, limit=5):
        """
        搜索相关的代码审查记录
        
        Args:
            query (str): 搜索关键词
            user_id (str, optional): 指定用户ID
            limit (int): 返回结果数量限制
        
        Returns:
            list: 搜索结果列表
        """
        try:
            search_results = self.memory.search(
                query,
                user_id=user_id,
                limit=limit
            )
            return True, search_results
        except Exception as e:
            return False, f"搜索记忆失败: {str(e)}"

    def delete_memories(self, user_id):
        """
        删除指定用户的所有记录
        
        Args:
            user_id (str): SVN提交者ID
        """
        try:
            self.memory.delete_all(user_id=user_id)
            return True, "记忆删除成功"
        except Exception as e:
            return False, f"记忆删除失败: {str(e)}"

# 创建单例实例
memory_client = MemoryClient() 