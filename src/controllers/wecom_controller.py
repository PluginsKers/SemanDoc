# 示例函数，根据消息类型处理企业微信消息
def handle_wecom_message(data):
    # 假设data是一个字典，包含了消息的类型和内容
    message_type = data.get("type")
    content = data.get("content")

    # 根据消息类型进行不同的处理
    if message_type == "text":
        # 处理文本消息
        return handle_text_message(content)
    elif message_type == "image":
        # 处理图片消息
        return handle_image_message(content)
    # 可以根据需要添加更多消息类型的处理逻辑
    else:
        # 未知的消息类型
        return {"error": "Unsupported message type"}


# 处理文本消息的示例函数
def handle_text_message(content):
    # 在这里实现处理文本消息的逻辑
    # 例如，回复相同的消息内容
    return {"type": "text", "content": f"Received your message: {content}"}


# 处理图片消息的示例函数
def handle_image_message(content):
    # 在这里实现处理图片消息的逻辑
    # 例如，简单地回复一个确认消息
    return {"type": "text", "content": "Received your image"}
