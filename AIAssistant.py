import json
import os
from openai import OpenAI
import jenkinstools

from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

client = OpenAI(api_key=os.getenv("AI_API_KEY"), base_url=os.getenv("AI_API_BASE"))

tools = [
    # 工具1 获取当前热更任务的状态
    {
        "type": "function",
        "function": {
            "name": "get_hotfix_jobs_status",
            "description": "获取当前热更任务的状态。",
            "parameters": {}  # 因为获取当前时间无需输入参数，因此parameters为空字典
        }
    },
    # 工具2 执行指定的热更任务
    {
        "type": "function",
        "function": {
            "name": "execute_hotfix_job",
            "description": "执行指定的热更任务。",
            "parameters": {
                "HotfixChannel": {
                    "type": "string",
                    "description": "热更对应的渠道，如果是开发测试服，则是devtest",
                    "enum": ["devtest", "douyintest", "ios"]
                },
                "TargetServer": {
                    "type": "string",
                    "description": "目标服务器，目前只允许指向Unity测试服",
                    "enum": ["Unity测试服", "检查点测试服"]
                },
                "PatchType": {
                    "type": "string",
                    "description": "打包方式，目前只支持BothAB_Code",
                    "enum": ["BothAB_Code", "OnlyCode", "OnlySubmit"]
                }
            }
        }
    }
]


def process_user_input(user_input):
    response = client.chat.completions.create(
        model=os.getenv("AI_MODEL"),
        messages=[
            {"role": "system", "content": "你是一个Jenkins任务管理助手。你可以帮助用户获取任务状态或执行任务。"},
            {"role": "user", "content": user_input}
        ],
        tools=tools,
        stream=False
    )

    message = response.choices[0].message

    if message.tool_calls is not None:
        tool_calls = message.tool_calls
        tool_calls = tool_calls[0]
        function_name = tool_calls.function.name
        arguments = json.loads(tool_calls.function.arguments)

        if function_name == "get_hotfix_jobs_status":
            result = jenkinstools.get_hotfix_job_status()
        elif function_name == "execute_hotfix_job":
            result = jenkinstools.execute_hotfix_job(**arguments)
        else:
            result = "未知的函数调用"

        return f"AI助手决定执行以下操作：\n{function_name}({arguments})\n\n结果：{result}"
    else:
        return message["content"]


if __name__ == "__main__":
    print(process_user_input("获取当前热更任务的状态"))
