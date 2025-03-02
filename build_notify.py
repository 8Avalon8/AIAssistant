import json
import os
import re
import subprocess
import sys
import locale
from datetime import datetime
from http import HTTPStatus
from feishu_notifier import FeishuNotifier
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

REQUIRED_PACKAGES = [
    'requests',
    'dashscope',
    'httpx',
    'openai>=1.0.0',
]

try:
    import pkg_resources
except ImportError:
    subprocess.call("pip install setuptools", shell=True)
    import pkg_resources

for package in REQUIRED_PACKAGES:
    try:
        dist = pkg_resources.get_distribution(package)
        print('{} ({}) is installed'.format(dist.key, dist.version))
    except pkg_resources.DistributionNotFound:
        print('{} is NOT installed'.format(package))
        subprocess.call([sys.executable, "-m", "pip", "install", package], shell=True)

import requests


token = os.getenv("AI_API_KEY")
endpoint = os.getenv("AI_API_BASE")
model_name = os.getenv("AI_MODEL")


PROMPT = """
你是一个游戏开发项目的SVN拟人助手，你负责审阅SVN提交日志和记录并进行总结，我会给你一段SVN提交日志
项目说明如下：
1.是一个Unity游戏开发项目
2.提交内容主要为cs文件代码、lua脚本代码、各种Unity资产、美术资产等
3.新增资源如果在Assets文件夹下，需要和对应meta文件一起提交
你幽默有趣,善于点评.
你可以评选一个最佳提交人，标准为：
1.提交日志描述清晰说明了提交内容、目的
2.不容易产生混肴
3.字数合理
4.为他给出正面评价
同时评选一个最差提交人，主要考察是否过于简单或者无法准确指明提交内容或者目的，或者提交文件可能和说明不一致。
1.提交日志字数过少
2.无法准确指明提交内容或者目的
3.提交文件和说明不一致
4.改动的文件可能涉及多个功能和修改但日志说明不一致
5.多次以相同的日志提交
6.给出负面评价
因为有些同事会习惯不好，如果他们有提交需要对他们进行单独的评论,没有则无需提及，以下是名单：
---
暂无
---
请保持提交人的用户名为英文，使用纯文本格式
"""

SYSTEM_PROMPT = "你是一个游戏开发项目的SVN助手。你负责审阅SVN提交日志和记录并进行总结，永远用中文回答，这是你的设定：\n"

HUMANSETTING = """
1.你是拥有现代软件工程项目管理技能的当代鲁迅，性能好奇、坦率、睿智
2.你熟练掌握软件工程管理、熟练掌握SVN软件的使用
3.你擅长诘问、洞察、反思，用最简洁的对话
4.你的表达充满反讽、比喻、简介、深刻、启发
5.清楚地知道面对的是自己的开发者。
"""

# 设置编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

class BuildConfig:
    def __init__(self):
        # AI配置
        self.token = token
        self.endpoint = endpoint
        self.model_name = model_name
        
        # 环境变量配置
        self.job_name = os.environ.get('JOB_NAME', '')
        self.build_number = os.environ.get('BUILD_NUMBER', '')
        self.build_url = os.environ.get('BUILD_URL', '')
        self.update_svn = os.environ.get('UpdateSVN', '')
        self.hotfix_type = os.environ.get('HotfixType', '')
        self.hotfix_channel = os.environ.get('HotfixChannel', '')
        self.hotfix_desc = os.environ.get('HotfixDesc', '')
        self.target_server = os.environ.get('TargetServer', '')
        self.patch_type = os.environ.get('PatchType', '')
        self.workspace = os.environ.get('WORKSPACE', '')
        self.show_ai_assistance = os.environ.get('ShowAIAssistance', '')

    def update_config(self, workspace=None, show_ai=None):
        if workspace:
            self.workspace = workspace
        if show_ai is not None:
            self.show_ai_assistance = "true"

def format_svn_log(log_content):
    """
    格式化SVN日志内容
    
    Args:
        log_content (str): SVN日志原始内容
    
    Returns:
        str: 格式化后的日志内容
    """
    result = []
    current_revision = None
    current_author = None
    current_message_lines = []
    
    for line in log_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('Changed paths:') or line.startswith('---'):
            # 如果遇到空行、Changed paths或分隔线，且已经收集了一条完整的提交信息
            if current_revision and current_author and current_message_lines:
                message = '\n'.join(current_message_lines)
                result.append(f"{current_revision} {current_author} {message}")
                current_message_lines = []
            continue
            
        if line.startswith('r'):
            # 新的提交记录开始
            parts = line.split('|')
            if len(parts) >= 2:
                current_revision = parts[0].strip()[1:]  # 去掉 'r' 前缀
                current_author = parts[1].strip()
                current_message_lines = []
        else:
            # 提交信息行
            current_message_lines.append(line)
    
    # 处理最后一条记录
    if current_revision and current_author and current_message_lines:
        message = '\n'.join(current_message_lines)
        result.append(f"{current_revision} {current_author} {message}")
    
    return '\n'.join(result)

### 调用AI助手
def call_with_stream(content: str, config: BuildConfig):
    messages = [
        {'role': 'system',
            'content': SYSTEM_PROMPT + HUMANSETTING},
        {'role': 'user', 'content': PROMPT + content}
    ]
    from openai import OpenAI
    try:
        client = OpenAI(api_key=config.token, base_url=config.endpoint)
        completion = client.chat.completions.create(
            model=config.model_name,
            messages=messages,
            top_p=0.7,
            temperature=1.0
        )
        return completion.choices[0].message.content 
    except Exception as e:
        print(f"AI助手已阵亡: {e}")
            
            
def get_svn_logs(workspace, previous_revision, current_revision, username="username", password="password"):
    """
    获取SVN日志信息
    
    Args:
        workspace (str): 工作目录路径
        previous_revision (str): 起始版本号
        current_revision (str): 结束版本号
        username (str): SVN用户名
        password (str): SVN密码
        
    Returns:
        tuple: (详细日志, 简单日志, 格式化后的日志)
    """
    svn_command_for_AI = f'svn log -v -r {previous_revision}:{current_revision} {workspace}/DR22 --non-interactive --trust-server-cert'
    svn_command_simple = f'svn log -r {previous_revision}:{current_revision} {workspace}/DR22 --non-interactive --trust-server-cert'
    
    try:
        SVN_LOG = subprocess.check_output(svn_command_for_AI, shell=True, stderr=subprocess.STDOUT)
        SVN_SIMPLE_LOG = subprocess.check_output(svn_command_simple, shell=True, stderr=subprocess.STDOUT)
        
        try:
            SVN_LOG = SVN_LOG.decode('utf-8')
            SVN_SIMPLE_LOG = SVN_SIMPLE_LOG.decode('gbk')
        except UnicodeDecodeError:
            SVN_LOG = SVN_LOG.decode('gbk')
            SVN_SIMPLE_LOG = SVN_SIMPLE_LOG.decode('gbk')
            
        formatted_output = format_svn_log(SVN_SIMPLE_LOG)
        return SVN_LOG, SVN_SIMPLE_LOG, formatted_output
    except subprocess.CalledProcessError as e:
        print(f"执行SVN命令时出错: {e}")
        print(f"命令输出: {e.output}")
        raise

def main(workspace=None, show_ai=None):
    config = BuildConfig()
    config.update_config(workspace, show_ai)
    
    # 输出获取的环境变量值
    print("获取到的环境变量值:")
    print(f"JOB_NAME: {config.job_name}")
    print(f"BUILD_NUMBER: {config.build_number}")
    print(f"BUILD_URL: {config.build_url}")
    print(f"UpdateSVN: {config.update_svn}")
    print(f"HotfixType: {config.hotfix_type}")
    print(f"HotfixChannel: {config.hotfix_channel}")
    print(f"HotfixDesc: {config.hotfix_desc}")
    print(f"TargetServer: {config.target_server}")
    print(f"PatchType: {config.patch_type}")
    print(f"WORKSPACE: {config.workspace}")
    print(f"ShowAIAssistance: {config.show_ai_assistance}")

    # 读取SVN版本号
    with open(os.path.join(config.workspace, 'previous_revision.txt'), 'r') as f:
        PREVIOUS_REVISION = f.read().strip()
    with open(os.path.join(config.workspace, 'current_revision.txt'), 'r') as f:
        CURRENT_REVISION = f.read().strip()

    # 检查之前步骤的执行结果
    if os.environ.get('BUILD_EXIT_CODE', '0') != '0':
        STATUS = "失败"
        BUILD_EXIT_CODE = os.environ.get('BUILD_EXIT_CODE', '1')
    else:
        STATUS = "成功"
        BUILD_EXIT_CODE = '0'

    # 获取SVN日志，包括修改的文件
    svn_command_for_AI = f'svn log -v -r {PREVIOUS_REVISION}:{CURRENT_REVISION} {config.workspace}/DR22 --non-interactive --trust-server-cert'
    svn_command_simple = f'svn log -r {PREVIOUS_REVISION}:{CURRENT_REVISION} {config.workspace}/DR22 --non-interactive --trust-server-cert'
    try:
        SVN_LOG = subprocess.check_output(svn_command_for_AI, shell=True, stderr=subprocess.STDOUT)
        SVN_SIMPLE_LOG = subprocess.check_output(svn_command_simple, shell=True, stderr=subprocess.STDOUT)
        try:
            SVN_LOG = SVN_LOG.decode('utf-8')
            SVN_SIMPLE_LOG = SVN_SIMPLE_LOG.decode('utf-8')
        except UnicodeDecodeError:
            SVN_LOG = SVN_LOG.decode('gbk')
            SVN_SIMPLE_LOG = SVN_SIMPLE_LOG.decode('gbk')

        formatted_output = format_svn_log(SVN_SIMPLE_LOG)
        if config.show_ai_assistance != 'true':
            finalResult = ""
        else:
            finalResult = call_with_stream(SVN_LOG, config)
    except subprocess.CalledProcessError as e:
        print(f"执行SVN命令时出错: {e}")
        print(f"命令输出: {e.output}")
        sys.exit(1)

    hotfix_args = f"""
        是否更新SVN: {config.update_svn}
        热更类型: {config.hotfix_type}
        热更渠道: {config.hotfix_channel}
        热更说明: {config.hotfix_desc}
        目标服务器: {config.target_server}
        PatchType: {config.patch_type}
        更新前SVN版本: {PREVIOUS_REVISION}
        当前SVN版本: {CURRENT_REVISION}
        """
    
    print(finalResult)
    
    # 初始化飞书通知器
    notifier = FeishuNotifier(
        app_id=os.getenv("FEISHU_APP_ID"),
        app_secret=os.getenv("FEISHU_APP_SECRET")
    )
    
    # 发送飞书消息
    success = notifier.send_message(
        config.job_name,
        config.build_number,
        STATUS,
        hotfix_args,
        formatted_output,
        finalResult
    )
    
    if not success:
        sys.exit(1)

    # Set exit code based on build result
    sys.exit(int(BUILD_EXIT_CODE))

if __name__ == "__main__":
    main()
    #main('E:\\DR22Android_22',True)
    #main('C:\\hanjiajianghu2',True)