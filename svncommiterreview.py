import subprocess
import os
import difflib
import openai
from openai import OpenAI
import random
import re
from feishu_notifier import FeishuNotifier
from dotenv import load_dotenv
from string import Template

# 加载.env文件中的环境变量
load_dotenv()

def run_command(cmd):
    """运行命令并返回输出，处理编码问题"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', shell=True)
        return result.stdout
    except UnicodeDecodeError:
        # 如果UTF-8解码失败，尝试使用GBK
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='gbk', errors='replace', shell=True)
        return result.stdout

def get_svn_diff(repo_path, revision):
    """获取指定SVN修订版本的差异"""
    cmd = f'svn diff -c {revision} {repo_path} {os.environ["USER_INFO"]}'
    return run_command(cmd)

def filter_lua_files(diff_content):
    """过滤出.lua文件的差异"""
    lines = diff_content.split('\n')
    lua_diffs = []
    current_file = None
    for line in lines:
        if line.startswith('Index: ') and line.endswith('.lua'):
            current_file = line[7:]
            lua_diffs.append(f"Changes in {current_file}:\n")
        elif current_file:
            lua_diffs.append(line)
    return '\n'.join(lua_diffs)

def get_commit_message(repo_path, revision):
    """获取提交日志"""
    cmd = f'svn log -r {revision} {repo_path} {os.environ["USER_INFO"]}'
    return run_command(cmd)


def analyze_with_openai(diff_content, commit_message, current_file):
    """使用OpenAI API分析差异和提交信息"""
    
    # 从文件加载提示词模板
    prompt_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts", "lua_review_prompt.txt")
    try:
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
    except FileNotFoundError:
        # 如果找不到文件，使用默认提示词
        print(f"警告：找不到提示词模板文件 {prompt_file_path}，使用默认提示词")
        prompt_template = """
        Analyze the following SVN commit and current file content:
        
        1. 提交信息:
        $commit_message
        
        2. 改动内容:
        $diff_content
        
        3. 当前文件内容:
        $current_file
        
        Please provide your analysis in Chinese.
        """
    
    # 使用更安全的方式进行变量替换
    # 首先定义要替换的变量字典
    variables = {
        "commit_message": commit_message,
        "diff_content": diff_content,
        "current_file": current_file
    }
    
    # 使用Template类进行安全替换
    template = Template(prompt_template)
    prompt = template.safe_substitute(variables)
    
    client = OpenAI(
        base_url=os.environ["OPENAI_API_BASE"],
        api_key=os.environ["OPENAI_API_KEY"],
    )
    print(os.environ["OPENAI_API_BASE"])
    print(os.environ["OPENAI_API_KEY"])
    print(os.environ["OPENAI_MODEL"])
    response = client.chat.completions.create(
        model=os.environ["OPENAI_MODEL"],
        messages=[
            {"role": "system", "content": "You are a code review assistant specialized in Lua programming."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4096,
        top_p=1.0,
    )

    return response.choices[0].message.content

def get_revisions_between(repo_path, start_rev, end_rev):
    """获取两个版本之间的所有提交记录"""
    cmd = f'svn log -r {start_rev}:{end_rev} {repo_path} {os.environ["USER_INFO"]}'
    log_content = run_command(cmd)
    
    # 使用正则表达式解析日志，提取修订版本号
    revision_pattern = r'^r(\d+) \|'
    revisions = re.findall(revision_pattern, log_content, re.MULTILINE)
    return revisions

def has_lua_changes(repo_path, revision):
    """检查某个提交是否包含lua文件的改动"""
    diff_content = get_svn_diff(repo_path, revision)
    lua_diff = filter_lua_files(diff_content)
    return bool(lua_diff.strip())

def get_lua_revisions(repo_path, start_rev, end_rev):
    """获取包含lua文件改动的所有提交"""
    all_revisions = get_revisions_between(repo_path, start_rev, end_rev)
    lua_revisions = []
    
    print(f"正在检查 {len(all_revisions)} 个提交...")
    for rev in all_revisions:
        if has_lua_changes(repo_path, f"r{rev}"):
            lua_revisions.append(f"r{rev}")
            print(f"发现包含lua改动的提交: r{rev}")
    
    return lua_revisions

def send_feishu_notification(analysis):
    """发送飞书通知"""
    notifier = FeishuNotifier(
        app_id=os.getenv("FEISHU_APP_ID"),
        app_secret=os.getenv("FEISHU_APP_SECRET")
    )
    
    success, message = notifier.send_simple_card_message(
        chat_id=os.getenv("FEISHU_LUA_REVIEW_CHAT_ID"),  # luaReview测试群
        title="LuaReview",
        content=analysis
    )
    
    # if success:
    #     print("消息发送成功")

    # else:
    #     print(f"消息发送失败: {message}")

def get_current_file_content(repo_path, file_path):
    """获取指定文件的当前内容"""
    cmd = f'svn cat {repo_path}/{file_path} {os.environ["USER_INFO"]}'
    return run_command(cmd)
    
def main(repo_path, start_rev, end_rev, send_to_feishu=False):
    from memory_client import MemoryClient, memory_client
    memory_client = MemoryClient()
    # 获取所有包含lua改动的提交
    lua_revisions = get_lua_revisions(repo_path, start_rev, end_rev)
    
    if not lua_revisions:
        print("在指定版本范围内没有找到包含lua文件改动的提交。")
        return
    
    # 随机选择一个提交进行分析
    selected_revision = random.choice(lua_revisions)
    print(f"\n随机选择提交 {selected_revision} 进行分析...")
    
    # 获取SVN差异和提交信息
    diff_content = get_svn_diff(repo_path, selected_revision)


    # 从diff内容中提取修改的文件路径
    modified_files = []
    for line in diff_content.split('\n'):
        if line.startswith('Index: '):
            file_path = line[7:]  # 去掉"Index: "前缀
            modified_files.append(file_path)

    # 获取所有修改文件的当前内容
    current_file = ""
    for file_path in modified_files:
        current_file += f"\n=== {file_path} ===\n"
        current_file += get_current_file_content(repo_path, file_path)
    lua_diff = filter_lua_files(diff_content)
    commit_message = get_commit_message(repo_path, selected_revision)
    
    # 使用OpenAI分析
    analysis = analyze_with_openai(lua_diff, commit_message, current_file)
    
    if analysis:
        # 获取提交者ID
        committer = commit_message.split("|")[1].strip()
        # 保存分析结果到Memory
        success, message = memory_client.add_memory(
            content=analysis,
            user_id=committer,
            output_format="code_review"
        )
        if not success:
            print(f"保存分析结果失败: {message}")
            
        print("\n分析结果：")
        print(analysis)
        
        if send_to_feishu:
            send_feishu_notification(analysis)
    else:
        print("没有分析结果")

def get_last_svn_revision(repo_path):
    cmd = f'svn info {repo_path} {os.environ["USER_INFO"]}'
    output = run_command(cmd)
    # 使用正则表达式提取版本号
    revision_match = re.search(r'Revision: (\d+)', output)
    if revision_match:
        return int(revision_match.group(1))
    raise Exception("无法获取SVN版本号")

if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = os.getenv("AI_API_KEY")
    os.environ["OPENAI_API_BASE"] = os.getenv("AI_API_BASE")
    os.environ["OPENAI_MODEL"] = os.getenv("AI_MODEL")
    os.environ["USER_INFO"] = f" --non-interactive --trust-server-cert"
    os.environ["MEM0_API_KEY"] = os.getenv("MEM0_API_KEY")
    repo_path = "C:/hanjiajianghu2/DR22"
    # 然后再获取版本号
    end_rev = get_last_svn_revision(repo_path)
    start_rev = end_rev - 20
    # 转string
    start_rev = str(start_rev)
    end_rev = str(end_rev)
    main(repo_path, start_rev, end_rev, send_to_feishu=True)