def expand_string(text, length):
    return text.ljust(length)

# 使用示例
original_text = "Hello"
expanded_text = expand_string(original_text, 10)
print(f"'{expanded_text}'")  # 输出: 'Hello     '，总长度为10，右侧填充空格
