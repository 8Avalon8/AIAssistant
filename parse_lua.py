from tree_sitter import Language, Parser
import tree_sitter_lua
from dataclasses import dataclass
from typing import List, Optional, Dict
import os
from pathlib import Path

@dataclass
class CodeChunk:
    """代码块的数据类"""
    function_name: str  # 函数名
    content: str  # 原始代码文本
    start_line: int  # 起始行号
    end_line: int  # 结束行号
    metadata: Dict  # 元数据
    parameters: List[str]  # 函数参数列表
    is_local: bool  # 是否为局部函数
    comments: List[str]  # 函数前的注释

class LuaASTParser:
    def __init__(self):
        self.parser = Parser()
        self.parser.language = Language(tree_sitter_lua.language())
        self.source_code = None
        self.file_path = None

    def parse_file(self, file_path: str) -> List[CodeChunk]:
        """解析单个 Lua 文件并返回函数代码块列表"""
        self.file_path = file_path
        with open(file_path, 'rb') as f:
            self.source_code = f.read()
        
        tree = self.parser.parse(self.source_code)
        return self._extract_functions(tree.root_node)

    def parse_directory(self, directory_path: str) -> Dict[str, List[CodeChunk]]:
        """递归解析目录下的所有 Lua 文件"""
        result = {}
        directory = Path(directory_path)
        
        # 递归查找所有 .lua 文件
        for lua_file in directory.rglob("*.lua"):
            try:
                chunks = self.parse_file(str(lua_file))
                if chunks:  # 只添加包含函数的文件
                    result[str(lua_file)] = chunks
            except Exception as e:
                print(f"解析文件 {lua_file} 时出错: {str(e)}")
        
        return result

    def _get_node_text(self, node) -> str:
        """获取节点的原始代码文本"""
        return self.source_code[node.start_byte:node.end_byte].decode()

    def _get_previous_comments(self, node) -> List[str]:
        """获取节点前的注释"""
        comments = []
        current = node.prev_sibling
        while current and current.type == 'comment':
            comments.append(self._get_node_text(current))
            current = current.prev_sibling
        return list(reversed(comments))  # 反转列表以保持注释的原始顺序

    def _extract_parameters(self, params_node) -> List[str]:
        """提取函数参数列表"""
        if not params_node:
            return []
        
        params = []
        for child in params_node.children:
            if child.type == 'identifier':
                params.append(self._get_node_text(child))
            elif child.type == 'vararg_expression':
                params.append('...')
        return params

    def _extract_function_name(self, node) -> Optional[str]:
        """提取函数名"""
        if node.type == 'function_declaration':
            name_node = node.child_by_field_name('name')
            if name_node:
                if name_node.type == 'identifier':
                    return self._get_node_text(name_node)
                elif name_node.type == 'variable':
                    # 处理 table.method 形式的函数名
                    table_node = name_node.child_by_field_name('table')
                    method_node = name_node.child_by_field_name('method')
                    if table_node and method_node:
                        return f"{self._get_node_text(table_node)}.{self._get_node_text(method_node)}"
        elif node.type == 'local_function_declaration':
            name_node = node.child_by_field_name('name')
            if name_node and name_node.type == 'identifier':
                return self._get_node_text(name_node)
        return None

    def _extract_functions(self, node) -> List[CodeChunk]:
        """提取所有函数定义"""
        functions = []
        
        # 递归处理子节点
        for child in node.children:
            # 处理函数定义语句
            if child.type in ['function_declaration']:
                function_name = self._extract_function_name(child)
                if function_name:
                    # 提取参数
                    params_node = child.child_by_field_name('parameters')
                    parameters = self._extract_parameters(params_node)
                    
                    # 获取函数前的注释
                    comments = self._get_previous_comments(child)
                    
                    # 创建代码块
                    chunk = CodeChunk(
                        function_name=function_name,
                        content=self._get_node_text(child),
                        start_line=child.start_point[0] + 1,
                        end_line=child.end_point[0] + 1,
                        metadata={
                            'file_path': self.file_path,
                            'start_line': child.start_point[0] + 1,
                            'end_line': child.end_point[0] + 1,
                            'start_column': child.start_point[1],
                            'end_column': child.end_point[1],
                        },
                        parameters=parameters,
                        is_local=child.type == 'local_function_definition_statement',
                        comments=comments
                    )
                    functions.append(chunk)
        
        return functions

    def print_chunks(self, chunks_by_file: Dict[str, List[CodeChunk]]):
        """打印所有文件中的函数代码块"""
        for file_path, chunks in chunks_by_file.items():
            print(f"\n文件: {file_path}")
            print("=" * 80)
            for chunk in chunks:
                print(f"函数名: {chunk.function_name}")
                print(f"类型: {'局部函数' if chunk.is_local else '全局函数'}")
                print(f"参数: {chunk.parameters}")
                print(f"行号: {chunk.start_line}-{chunk.end_line}")
                if chunk.comments:
                    print("注释:")
                    for comment in chunk.comments:
                        print(f"  {comment}")
                print(f"元数据: {chunk.metadata}")
                print(f"内容:\n{chunk.content}")
                print("-" * 80)

def main():
    parser = LuaASTParser()
    # lua文件夹
    lua_folder = 'S:\DR22Main\DR22\data\lua'
    # 解析目录下的所有 Lua 文件
    chunks_by_file = parser.parse_directory(lua_folder)
    
    # 打印结果
    parser.print_chunks(chunks_by_file)
    
    # 将代码块保存在txt文件中
    with open('functions.txt', 'w', encoding='utf-8') as f:
        for file_path, chunks in chunks_by_file.items():
            f.write(f"\n文件: {file_path}\n")
            f.write("=" * 80 + "\n")
            for chunk in chunks:
                f.write(f"函数名: {chunk.function_name}\n")
                f.write(f"类型: {'局部函数' if chunk.is_local else '全局函数'}\n")
                f.write(f"参数: {chunk.parameters}\n")
                f.write(f"文件路径: {chunk.metadata['file_path']}\n")
                f.write(f"行号: {chunk.start_line}-{chunk.end_line}\n")
                if chunk.comments:
                    f.write("注释:\n")
                    for comment in chunk.comments:
                        f.write(f"  {comment}\n")
                f.write(f"内容:\n{chunk.content}\n")
                f.write("-" * 80 + "\n")

if __name__ == '__main__':
    main() 