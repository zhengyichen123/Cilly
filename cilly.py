import sys
from cilly_interpreter import cilly_eval, cilly_lexer, cilly_parser
import turtle

env = {
    "forward": lambda *args: turtle.forward(*args),
    "backward": lambda *args: turtle.backward(*args),
    "right": lambda *args: turtle.right(*args),
    "left": lambda *args: turtle.left(*args),
    "penup": lambda: turtle.penup(),
    "pendown": lambda: turtle.pendown(),
    "pencolor": lambda *args: turtle.pencolor(*args),
    "color": lambda *args: turtle.color(*args),
}


def reply():
    print("Cilly 交互式环境。输入 'exit' 退出，'load <文件>' 加载文件。")
    while True:
        buffer = []
        while True:
            try:
                prompt = "cilly> " if not buffer else "...... "
                line = input(prompt).strip()
                if line.lower() == "exit":
                    print("再见！")
                    sys.exit(0)
                if line.lower().startswith("load "):
                    filename = line.split(" ", 1)[1]
                    with open(filename, "r") as f:
                        code = f.read()
                    tokens = cilly_lexer(code)
                    # print(tokens)
                    ast = cilly_parser(tokens)
                    # print(ast)
                    cilly_eval(ast, env)
                    break
                if line:
                    buffer.append(line)
                code = "\n".join(buffer)
                if not code:
                    continue
                # 尝试解析代码
                tokens = cilly_lexer(code)
                # print(tokens)
                ast = cilly_parser(tokens)
                # print(ast)
                break  # 解析成功，退出输入循环
            except Exception as e:
                # print(e)
                if "期望" in str(e) and "eof" in str(e):
                    continue  # 需要更多输入
                elif "需要" in str(e):
                    continue
                else:
                    print(f"解析错误：{e}")
                    buffer = []
                    break
        if not buffer:
            continue
        try:
            # print(ast)
            result = cilly_eval(ast, env)
            if result is not None and result[1] is not None:
                print(result[1])
        except Exception as e:
            print(f"执行错误：{e}")


if __name__ == "__main__":
    reply()
