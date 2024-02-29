import xml.etree.ElementTree as ET
from src.modules.wecom.message import WecomMessage

from src import get_wecom_app, get_llm, get_docstore


async def handle_wecom_message(xml_str: str, **kwargs):
    app = get_wecom_app()
    xml_data = ET.fromstring(xml_str)

    kwargs.update({
        **kwargs,
        'msg_crypt': app.wxcpt
    })

    wecom_msg = WecomMessage(xml_str, **kwargs)
    sender = wecom_msg.get_sender()
    question = wecom_msg.get_content()
    mas_type = wecom_msg.get_msg_type()

    if not app.is_on_cooldown(sender) and mas_type == "text":
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

        app.send_message_async(sender, response, question)
