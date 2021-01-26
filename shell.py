import basic

# 不断接收键盘的输入
while True:
    text = input("basic >")
    res, error = basic.run('<stdin>', text)  # stdin 来自键盘
    if error:
        print(error.as_string())
    else:
        print(res)
