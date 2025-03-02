from feishu_notifier import FeishuNotifier
import os
from dotenv import load_dotenv

def main():
    # 加载.env文件中的环境变量
    load_dotenv()
    # 创建通知器实例
    notifier = FeishuNotifier(
        app_id=os.getenv("FEISHU_APP_ID"),
        app_secret=os.getenv("FEISHU_APP_SECRET")
    )

    # # 发送测试消息
    # success, message = notifier.send_text_message(
    #     chat_id="oc_5ef63ac5f50ede9f7dedeecc19200f62",
    #     text_content="test content"
    # )
    
    # 发送测试卡片
    success, message = notifier.send_simple_card_message(
        chat_id=os.getenv("FEISHU_TEST_CHAT_ID"),
        title="Review Result",
        content="test content"
    )



    if success:
        print("消息发送成功")

    else:
        print(f"消息发送失败: {message}")

if __name__ == "__main__":
    main()
