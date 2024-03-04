from src.modules.logging import logger
from src.modules.wecom.message import WecomMessage
from src import get_wecom_app, get_llm, get_docstore


def get_msg_info(xml_str: str, **kwargs):
    wecom_msg = WecomMessage(xml_str, **kwargs)
    sender = wecom_msg.get_sender()
    question = wecom_msg.get_content()
    msg_type = wecom_msg.get_msg_type()
    return sender, question, msg_type


async def handle_wecom_message(xml_str: str, **kwargs):
    sender = None  # Define sender initially to ensure it's available in the scope for error handling
    try:
        app = get_wecom_app()
        sender, question, msg_type = get_msg_info(xml_str, **kwargs)

        kwargs.update({
            'msg_crypt': app.wxcpt
        })

        if not app.is_on_cooldown(sender) and msg_type == "text":
            app.set_cooldown(sender, app.COOLDOWN_TIME)
            llm = get_llm()
            docs = await get_docstore().search(query=question, k=5)

            standardized_docs = "- " + \
                "\n- ".join(doc.page_content for doc in docs)

            records = app.historys.get(sender)
            history = [] if not records else records.get_raw_records()
            if history:
                summary = llm.get_summarize(history)
                reminder = llm.generate_sync(summary)
                history = [{"role": "user", "content": "总结一下上面我们聊了什么？"},
                           {"role": "assistant", "metadata": "", "content": reminder}]

            optimization = llm.get_optimize(standardized_docs, question)
            response = llm.generate_sync(optimization, history)

            await app.send_message_async(sender, response, question)
    except Exception as e:
        logger.exception(e)
        if sender:  # Ensure sender is defined
            error_response = "处理信息时出现问题，请稍后重试。"
            # Use await for asynchronous call
            await app.send_message_async(sender, error_response)
