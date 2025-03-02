import argparse
import subprocess
import sys
import os
from datetime import datetime, timedelta
from build_notify import call_with_stream, format_svn_log, BuildConfig
from feishu_notifier import FeishuNotifier

def get_svn_info(svn_url):
    """获取SVN仓库的最新版本号"""
    cmd = f'svn info {svn_url} --non-interactive --trust-server-cert'
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        try:
            result = result.decode('utf-8')
        except UnicodeDecodeError:
            result = result.decode('gbk')
        
        for line in result.split('\n'):
            if line.startswith('Revision:'):
                return line.split(':')[1].strip()
    except subprocess.CalledProcessError as e:
        print(f"获取SVN信息失败: {e}")
        print(f"错误输出: {e.output}")
        sys.exit(1)
    return None

def get_svn_logs_by_date(svn_url, start_date, end_date):
    """根据日期范围获取SVN日志"""
    cmd = f'svn log -v {svn_url} -r "{{{start_date}}}:{{{end_date}}}" --non-interactive --trust-server-cert'
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        try:
            result = result.decode('utf-8')
        except UnicodeDecodeError:
            result = result.decode('gbk')
        return result
    except subprocess.CalledProcessError as e:
        print(f"获取SVN日志失败: {e}")
        print(f"错误输出: {e.output}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='SVN提交记录分析工具')
    parser.add_argument('--svn_url', default='C:\\hanjiajianghu2\\DR22', help='SVN仓库地址')
    parser.add_argument('--username', default='username', help='SVN用户名')
    parser.add_argument('--password', default='password', help='SVN密码')


    parser.add_argument('--days', type=int, default=1, help='要分析的天数（默认7天）')
    
    args = parser.parse_args()
    
    # 计算日期范围
    end_date = datetime.now() + timedelta(days=1) # 加一天以包含今天的内容
    start_date = end_date - timedelta(days=args.days)
    
    # 格式化日期
    end_date_str = end_date.strftime('%Y-%m-%d')
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    print(f"分析时间范围: {start_date_str} 到 {end_date_str}")
    
    # 获取SVN日志
    svn_log = get_svn_logs_by_date(args.svn_url, start_date_str, end_date_str, args.username, args.password)
    
    # 格式化日志
    formatted_log = format_svn_log(svn_log)
    
    # 创建配置对象
    config = BuildConfig()
    
    print("\n=== SVN提交记录分析结果 ===")
    print(f"分析范围: {args.svn_url}")
    print(f"时间段: {start_date_str} 到 {end_date_str}")
    print("\n=== 原始提交记录 ===")
    print(formatted_log)
    
    # 调用AI助手进行分析
    print("\n正在分析提交记录...\n")
    analysis_result = call_with_stream(svn_log, config)
    
    
    print("\n=== AI分析结果 ===")
    print(analysis_result)
    notifier = FeishuNotifier()
    notifier.send_simple_card_message(
        chat_id=os.getenv("FEISHU_SVN_REVIEW_CHAT_ID"),
        title=f"今日SVN提交点评 ({start_date_str} to {end_date_str})",
        content=analysis_result
    )


if __name__ == "__main__":
    main() 