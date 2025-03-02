import os
import jenkins
import sys
import jenkins
import sys
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

def get_job_status(jenkins_url, username, password, job_name):
    try:
        # 连接到Jenkins服务器
        server = jenkins.Jenkins(jenkins_url, username=username, password=password)

        # 获取任务信息
        job_info = server.get_job_info(job_name)

        # 获取最后一次构建的编号
        last_build_number = job_info['lastBuild']['number']

        # 获取最后一次构建的详细信息
        build_info = server.get_build_info(job_name, last_build_number)

        # 获取构建结果
        result = build_info['result']

        # 获取构建状态
        building = build_info['building']

        # 获取构建的参数
        parameters = build_info['actions'][0]['parameters']

        # 格式化参数，取name和value
        parameters = "\n".join([f"{param['name']}={param['value']}" for param in parameters])

        if building:
            status = "正在进行中"
        else:
            status = result if result else "未知"

        return f"任务 '{job_name}' 的最新构建 (#{last_build_number}) 状态: {status}, 参数: {parameters}"

    except jenkins.JenkinsException as e:
        return f"发生错误: {str(e)}"


def get_hotfix_job_status():
    andorid_status = get_job_status(os.getenv("JENKINS_31_URL"), os.getenv("JENKINS_31_USERNAME"), os.getenv("JENKINS_31_PASSWORD"), "DR22安卓Branch热更")
    ios_status = get_job_status(os.getenv("JENKINS_39_URL"), os.getenv("JENKINS_39_USERNAME"), os.getenv("JENKINS_39_PASSWORD"), "DR22IOS热更")
    results = f"安卓热更任务状态: {andorid_status}\nIOS热更任务状态: {ios_status}"
    return results


def execute_job(job_name, parameters):
    try:
        # 连接到Jenkins服务器
        server31 = jenkins.Jenkins(os.getenv("JENKINS_31_URL"), username=os.getenv("JENKINS_31_USERNAME"), password=os.getenv("JENKINS_31_PASSWORD"))
        server39 = jenkins.Jenkins(os.getenv("JENKINS_39_URL"), username=os.getenv("JENKINS_39_USERNAME"), password=os.getenv("JENKINS_39_PASSWORD"))
        # 执行任务
        server31.build_job(job_name, parameters)
        server39.build_job(job_name, parameters)
        return f"任务 '{job_name}' 已经开始执行"
    except jenkins.JenkinsException as e:
        return f"发生错误: {str(e)}"


def execute_hotfix_job(channel: str, hotfix_desc: str, target_server: str, patch_type: str):
    return "暂时不允许"
    if channel == "android":
        job_name = "DR22安卓Branch热更"
    elif channel == "ios":
        job_name = "DR22IOS热更"
    else:
        return "未知的渠道"

    parameters = {
        "HotfixChannel": hotfix_desc,
        "TargetServer": target_server,
        "PatchType": patch_type
    }

    return execute_job(job_name, parameters)


if __name__ == "__main__":
    print(get_hotfix_job_status())
