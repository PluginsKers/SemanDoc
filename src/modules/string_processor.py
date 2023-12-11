class StringProcessor:
    def __init__(self):
        print(1)

    def replace_char_by_list(self, input_str: str, replace_char: list):
        for i in replace_char:
            input_str = input_str.replace(i[0], i[1])
        return input_str

    def split_by_punctuation(self, input_str: str):
        # 根据标点符号分割句子
        punctuation = ".!?。！？"
        sentences = []
        current_sentence = ""
        for char in input_str:
            if char not in punctuation:
                current_sentence += char
            else:
                current_sentence = current_sentence.strip()  # 移除句子两侧的空格
                if current_sentence:
                    sentences.append(current_sentence)
                current_sentence = ""
        if current_sentence:
            current_sentence = current_sentence.strip()
            sentences.append(current_sentence)
        return sentences


processor = StringProcessor()
