import streamlit as st
from sql import Lexer, Parser, Executor
import pandas as pd

# 初始化 Executor 并保存在 session_state 中以保持状态
if "executor" not in st.session_state:
    st.session_state.executor = Executor()

# 设置页面标题
st.title("SQL 翻译器")

# 提供使用说明
st.write("请输入 SQL 语句（支持多条语句，每条以分号结束）：")

# 创建一个文本输入框供用户输入 SQL 语句
sql_input = st.text_area(
    "SQL 输入",
    height=200,
    placeholder="示例：\nCREATE TABLE users(id INT, name String);\nINSERT INTO users VALUES (id = 1, name = 'Alice');\nSELECT name FROM users;",
)

# 创建一个执行按钮
if st.button("执行"):
    try:
        # 词法分析：将输入的 SQL 文本转换为 tokens
        lexer = Lexer(sql_input)
        tokens = lexer.tokenize()

        # 语法分析：将 tokens 转换为 AST
        parser = Parser(tokens)
        ast = parser.parse_program()
        print(ast)
        # 执行 AST 并获取结果
        results = st.session_state.executor.run(ast)

        # 检查 results 是否有效
        if results is None or not isinstance(results, (list, tuple)):
            st.error("执行失败：未返回有效结果")
        else:
            # 遍历执行结果并根据语句类型显示
            for result in results:
                if result is None:
                    st.write("语句执行失败")
                    continue
                stmt_type, stmt_result = result
                if stmt_type == "select":
                    st.write("查询结果：")
                    if stmt_result:  # 确保结果不为空
                        df = pd.DataFrame(stmt_result)
                        st.dataframe(df)  # 显示交互式表格
                    else:
                        st.write("无查询结果")
                else:
                    st.write(stmt_result)

    except Exception as e:
        # 显示错误信息
        st.error(f"错误：{str(e)}")

# 可选：提供一个示例 SQL 语句供用户参考
st.markdown("### 示例 SQL")
st.code(
    """
    CREATE TABLE users(id INT, name String);
    INSERT INTO users VALUES (id = 1, name = 'Alice');
    INSERT INTO users VALUES (id = 2, name = 'Bob');
    INSERT INTO users VALUES (id = 3, name = 'Charlie');
    INSERT INTO users VALUES (id = 4, name = 'David');
    INSERT INTO users VALUES (id = 5, name = 'Eve');
    INSERT INTO users VALUES (id = 6, name = 'Frank');
    CrEate table score(id INT, score INT);
    INSERT INTO score VALUES (id = 1, score = 90);
    INSERT INTO score (id, score) VALUES (2, 85);
    INSERT INTO score VALUES (id = 3, score = 80);
    INSERT INTO score VALUES (id = 4, score = 75);
    INSERT INTO score VALUES (id = 5, score = 70);
    INSERT INTO score VALUES (id = 6, score = 65);
    select * from score where score > 80;
    select name, score.score from users join score on users.id == score.id where users.name == 'Alice';
""",
    language="sql",
)
