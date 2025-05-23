﻿# Code generated by Lark OpenAPI.

import lark_oapi as lark
from lark_oapi.api.contact.v3 import *

if __name__ == '__main__':
    client = lark.Client.builder() \
        .app_id(os.getenv("FEISHU_APP_ID")) \
        .app_secret(os.getenv("FEISHU_APP_SECRET")) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()
    # 构造请求对象
    request: BatchGetIdUserRequest = BatchGetIdUserRequest.builder() \
        .user_id_type("open_id") \
        .request_body(BatchGetIdUserRequestBody.builder()
                      .emails(["xxxx@bytedance.com"])
                      .mobiles(["15000000000"])
                      .build()) \
        .build()
    # 发起请求
    response: BatchGetIdUserResponse = client.contact.v3.user.batch_get_id(request)
    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.contact.v3.user.batch_get_id failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")