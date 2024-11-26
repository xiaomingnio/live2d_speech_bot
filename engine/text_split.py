import re

def split_sentences(text):
    # 使用正则表达式匹配句子的结束标点 (例如 . ! ?)
    # 这里会包括标点符号和后面的空格或换行符
    pattern = re.compile(r'(?<=[。！？.!?])\s*')
    sentences = pattern.split(text)
    
    return sentences


def contains_punctuation(text, punctuation_list):
    return any(punc in text for punc in punctuation_list)


if __name__ == "__main__":
    # 示例字符串
    text = "Hello, world! Ho"

    # 分割句子
    sentences = split_sentences(text)

    # 输出结果
    for sentence in sentences:
        print(sentence)