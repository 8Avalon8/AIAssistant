import os
from flask import Flask
import lark_oapi as lark
from lark_oapi.adapter.flask import *

from im import *
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

#app = Flask(__name__)

def do_p2_im_message_receive_v1_new(data: lark.im.v1.P2ImMessageReceiveV1) -> None:
    #print(f'[ do_p2_im_message_receive_v1 access ], data: {lark.JSON.marshal(data, indent=4)}')
    # 输出message类型
    print(f'[ do_p2_im_message_receive_v1 access ], message type: {data.event.message.message_type}')
    # 输出群聊ID
    print(f'[ do_p2_im_message_receive_v1 access ], chat id: {data.event.message.chat_id}')
    # 输出用户ID
    print(f'[ do_p2_im_message_receive_v1 access ], sender id: {data.event.sender.sender_id.user_id}')
    # 输出消息内容
    print(f'[ do_p2_im_message_receive_v1 access ], message content: {data.event.message.content}')
    # 输出消息ID
    print(f'[ do_p2_im_message_receive_v1 access ], message id: {data.event.message.message_id}')
    # 输出消息时间
    print(f'[ do_p2_im_message_receive_v1 access ], message time: {data.event.message.create_time}')
    # 输出消息发送者类型
    print(f'[ do_p2_im_message_receive_v1 access ], sender type: {data.event.sender.sender_type}')
    # 输出消息发送者ID
    print(f'[ do_p2_im_message_receive_v1 access ], sender id: {data.event.sender.sender_id.open_id}')
    # 输出消息发送者ID
    print(f'[ do_p2_im_message_receive_v1 access ], sender id: {data.event.sender.sender_id.union_id}')
    # 输出消息发送者ID
    print(f'[ do_p2_im_message_receive_v1 access ], sender id: {data.event.sender.sender_id.user_id}')


def do_message_event(data: lark.CustomizedEvent) -> None:
    print(f'[ do_customized_event access ], type: message, data: {lark.JSON.marshal(data, indent=4)}')
    
# 注册事件回调
event_handler = lark.EventDispatcherHandler.builder(os.getenv("ENCRYPT_KEY"), os.getenv("VERIFICATION_TOKEN"), lark.LogLevel.DEBUG) \
    .register_p2_im_message_receive_v1(do_p2_im_message_receive_v1_new) \
    .register_p1_customized_event("message", do_message_event) \
    .build()


if __name__ == "__main__":
    cli = lark.ws.Client(os.getenv("APP_ID"),os.getenv("APP_SECRET"),
                         event_handler=event_handler,
                         log_level=lark.LogLevel.DEBUG)
    cli.start()
