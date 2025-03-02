# 提示词模板目录

此目录包含用于AI分析的提示词模板文件。

## 文件说明

- `lua_review_prompt.txt`: 用于Lua代码审查的提示词模板

## 使用方法

这些模板文件被`svncommiterreview.py`等脚本使用，通过字符串模板替换变量。

例如：
```python
from string import Template

with open("prompts/lua_review_prompt.txt", "r", encoding="utf-8") as f:
    prompt_template = f.read()
    
# 定义变量字典
variables = {
    "commit_message": commit_message,
    "diff_content": diff_content,
    "current_file": current_file
}

# 使用Template类进行安全替换
template = Template(prompt_template)
prompt = template.safe_substitute(variables)
```

## 注意事项

- 模板文件中使用`$variable_name`格式的占位符（不使用花括号）
- 如果需要在文本中包含美元符号`$`，请使用`$$`转义
- 这些文件通常包含敏感或特定项目的信息，因此在`.gitignore`中被忽略
- 如需添加新模板，请在此README中更新说明 