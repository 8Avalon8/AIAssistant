import lark_oapi as lark
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

client = lark.Client.builder() \
    .app_id(os.getenv("FEISHU_APP_ID")) \
    .app_secret(os.getenv("FEISHU_APP_SECRET")) \
    .log_level(lark.LogLevel.DEBUG) \
    .build()
