# 调用函数
from build_notify import get_svn_logs


detailed_log, simple_log, formatted_log = get_svn_logs(
    workspace="C:\\hanjiajianghu2",
    previous_revision="50201",
    current_revision="50430"
)

print(detailed_log)
print(simple_log)
print(formatted_log)