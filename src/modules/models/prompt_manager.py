class PromptManager:
    def get_summarize(self, dialogue_content: str):
        """
        Generates a prompt for summarizing dialogue content.

        :param dialogue_content: The text content of a dialogue.
        :return: A prompt for generating a summary of the dialogue.
        """
        prompt = f"# 请根据以下对话内容生成一个摘要\n\n{dialogue_content}"
        return prompt

    def get_optimize(self, knowledges: str, question: str):
        """
        Generates a prompt to refine knowledges text related to a question.

        :param knowledges: Text containing information or context.
        :param question: A specific question that needs answering.
        :return: A prompt for refining the knowledges text to be more relevant to the question.
        """
        prompt = f"# 获取与问题相关的信息\n\n## 信息：\n{knowledges}\n\n## 问题：\n{question}"
        return prompt
