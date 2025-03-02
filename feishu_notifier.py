import json
import requests
from datetime import datetime
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class FeishuNotifier:
    def __init__(self, app_id = os.getenv("FEISHU_APP_ID"), app_secret = os.getenv("FEISHU_APP_SECRET")):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn/open-apis"
        # 初始化 lark client
        self.client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()
        
    def get_tenant_access_token(self):
        """获取飞书tenant access token"""
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                return result.get("tenant_access_token"), result.get("expire")
            else:
                raise Exception(f"Error: {result.get('msg')}")
        else:
            raise Exception(f"HTTP request failed with status code: {response.status_code}")
            
    def send_message(self, job_name, build_number, status, hotfix_args, formatted_output, final_result):
        """发送飞书消息"""
        token, expire_time = self.get_tenant_access_token()
        print(f"Tenant Access Token: {token}")
        print(f"Expires in: {expire_time} seconds")
        
        url = f"{self.base_url}/im/v1/messages?receive_id_type=chat_id"
        
        payload = {
            "receive_id": os.getenv("FEISHU_BUILD_NOTIFY_CHAT_ID"),
            "msg_type": "interactive",
            "content": json.dumps({
                "type": "template",
                "data": {
                    "template_id": "AAqHQEn1zcQbq",
                    "template_variable": {
                        "title": f"[{job_name}] #{build_number} {status}",
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "hotfix_args": hotfix_args,
                        "hotfix_content": formatted_output,
                        "ai_judge": final_result
                    }
                }
            })
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"发送消息失败: {e}")
            print(response.text)
            return False 
        
    def send_card_message(self, chat_id, card_content):
        """发送卡片消息"""
        request: CreateMessageRequest = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(CreateMessageRequestBody.builder()
                          .receive_id(chat_id)
                          .msg_type("interactive")
                          .content(json.dumps(card_content))
                          .build()) \
            .build()

        response: CreateMessageResponse = self.client.im.v1.message.create(request)

        if not response.success():
            error_msg = f"发送消息失败, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
            lark.logger.error(error_msg)
            return False, error_msg

        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return True, "消息发送成功"
    
    def send_simple_card_message(self, chat_id,title,content):
        """发送简单卡片消息"""
        json = { "type": "template",
                "data": {
                    "template_id": "AAqC36rf8W5iW",
                    "template_variable": {
                        "title": title,
                        "content": content,
                    }

                }}
        return self.send_card_message(chat_id, json)
    

    def send_text_message(self, chat_id, text_content):
        """发送普通文本消息"""
        request: CreateMessageRequest = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(CreateMessageRequestBody.builder()
                          .receive_id(chat_id)
                          .msg_type("text")
                          .content(json.dumps({"text": text_content}))
                          .build()) \
            .build()

        response: CreateMessageResponse = self.client.im.v1.message.create(request)

        if not response.success():
            error_msg = f"发送消息失败, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
            lark.logger.error(error_msg)
            return False, error_msg

        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        return True, "消息发送成功" 