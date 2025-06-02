import streamlit as st
from sql import Lexer, Parser, Executor
import pandas as pd

# 初始化 Executor 并保存在 session_state 中以保持状态
if "executor" not in st.session_state:
    st.session_state.executor = Executor()

# 初始化 tables_data
if "tables_data" not in st.session_state:
    st.session_state.tables_data = {}


# 重置所有表的显示状态
def reset_tables_data():
    # 确保只处理有数据的情况
    if hasattr(st.session_state.executor, 'tables'):
        for table_name, table_info in st.session_state.executor.tables.items():
            # 创建表的数据框架
            columns = list(table_info["columns"].keys())
            data = table_info["data"]

            # 转换为DataFrame
            if data:
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame(columns=columns)

            st.session_state.tables_data[table_name] = df


# 更新表格显示
def update_tables_display():
    # 确保在数据变化后更新状态
    if hasattr(st.session_state.executor, 'tables'):
        reset_tables_data()

    #st.subheader("数据库表状态")

    if not st.session_state.tables_data:
        st.info("数据库为空，请创建表并插入数据。")
        return

    # 为每个表创建一个选项卡展示
    tab_list = list(st.session_state.tables_data.keys())
    tabs = st.tabs(tab_list)

    # 为每个表创建一个单独的选项卡
    for i, table_name in enumerate(tab_list):
        with tabs[i]:
            st.subheader(f"表: {table_name}")

            df = st.session_state.tables_data[table_name]

            if df.empty:
                st.info("表为空")
            else:
                # 显示完整表格
                st.dataframe(
                    df,
                    use_container_width=True,
                )


# 首次运行时初始化tables_data
if "tables_data" not in st.session_state or not st.session_state.tables_data:
    st.session_state.tables_data = {}
    reset_tables_data()

# 设置页面标题
st.title("SQL 翻译器")

# 创建侧边栏
with st.sidebar:
    st.subheader("测试样例")

    # 测试样例代码
    st.code("""
    CREATE TABLE users(id INT, name STRING, age INT);
    CREATE TABLE orders(id INT, user_id INT, amount FLOAT, status STRING);
    CREATE TABLE products(id INT, name STRING, price FLOAT, stock INT);
    
    INSERT INTO users VALUES (id = 1, name = 'Alice', age = 25);
    INSERT INTO users VALUES (id = 2, name = 'Bob', age = 30);
    INSERT INTO users VALUES (id = 3, name = 'Charlie', age = 22);
    INSERT INTO users VALUES (id = 4, name = 'David', age = 28);
    INSERT INTO orders (id, user_id, amount, status) VALUES (1, 1, 100.5, 'paid');
    INSERT INTO orders VALUES (id = 2, user_id = 2, amount = 200.75, status = 'pending');
    INSERT INTO orders VALUES (id = 3+1, user_id = 2 * 1, amount = 50.0 * 3, status = 'paid');
    INSERT INTO orders VALUES (id = 4, user_id = 3, amount = 75.25, status = 'pending');
    INSERT INTO products VALUES (id = 1, name = 'Laptop', price = 999.99, stock = 10);
    INSERT INTO products VALUES (id = 2, name = 'Phone', price = 699.99, stock = 20);
    INSERT INTO products VALUES (id = 3, name = 'Tablet', price = 399.99, stock = 15);
    
    SELECT * FROM users;
    SELECT name, age FROM users WHERE age > 25;
    SELECT users.name, orders.amount, orders.status FROM users JOIN orders ON users.id == orders.user_id;
    
    UPDATE products SET stock = 5 WHERE id == 1;
    SELECT * FROM products;
    
    DELETE FROM orders WHERE amount < 100 AND status == 'pending';
    DELETE FROM users WHERE id == 4;
    """, language="sql")

    # 加载样例按钮
    if st.button("加载样例到编辑器"):
        st.session_state.sql_input = """
        CREATE TABLE users(id INT, name STRING, age INT);
        CREATE TABLE orders(id INT, user_id INT, amount FLOAT, status STRING);
        CREATE TABLE products(id INT, name STRING, price FLOAT, stock INT);
        
        INSERT INTO users VALUES (id = 1, name = 'Alice', age = 25);
        INSERT INTO users VALUES (id = 2, name = 'Bob', age = 30);
        INSERT INTO users VALUES (id = 3, name = 'Charlie', age = 22);
        INSERT INTO users VALUES (id = 4, name = 'David', age = 28);
        INSERT INTO orders (id, user_id, amount, status) VALUES (1, 1, 100.5, 'paid');
        INSERT INTO orders VALUES (id = 2, user_id = 2, amount = 200.75, status = 'pending');
        INSERT INTO orders VALUES (id = 3+1, user_id = 2 * 1, amount = 50.0 * 3, status = 'paid');
        INSERT INTO orders VALUES (id = 4, user_id = 3, amount = 75.25, status = 'pending');
        INSERT INTO products VALUES (id = 1, name = 'Laptop', price = 999.99, stock = 10);
        INSERT INTO products VALUES (id = 2, name = 'Phone', price = 699.99, stock = 20);
        INSERT INTO products VALUES (id = 3, name = 'Tablet', price = 399.99, stock = 15);
        
        SELECT * FROM users;
        SELECT name, age FROM users WHERE age > 25;
        SELECT users.name, orders.amount, orders.status FROM users JOIN orders ON users.id == orders.user_id;
        
        UPDATE products SET stock = 5 WHERE id == 1;
        SELECT * FROM products;
        
        DELETE FROM orders WHERE amount < 100 AND status == 'pending';
        DELETE FROM users WHERE id == 4;
        """
        st.success("测试样例已加载到编辑器中")

# 主内容区域
col1, col2 = st.columns([1, 1])

with col1:
    # 提供使用说明
    st.write("请输入 SQL 语句（支持多条语句，每条以分号结束）：")

    # 创建一个文本输入框供用户输入 SQL 语句
    sql_input = st.text_area(
        "SQL 输入",
        height=200,
        placeholder="示例：\nCREATE TABLE users(id INT, name String);\nINSERT INTO users VALUES (id = 1, name = 'Alice');\nSELECT name FROM users;",
        key="sql_input" if "sql_input" in st.session_state else None
    )

    # 创建一个执行按钮
    if st.button("执行"):
        try:
            if not sql_input.strip():
                st.warning("请输入有效的 SQL 语句")
            else:
                # 词法分析：将输入的 SQL 文本转换为 tokens
                lexer = Lexer(sql_input)
                tokens = lexer.tokenize()

                # 语法分析：将 tokens 转换为 AST
                parser = Parser(tokens)
                ast = parser.parse_program()

                # 执行 AST 并获取结果
                results = st.session_state.executor.run(ast)

                # 更新表的显示状态
                reset_tables_data()

                # 检查 results 是否有效
                if results is None or not isinstance(results, (list, tuple)):
                    st.error("执行失败：未返回有效结果")
                else:
                    # 遍历执行结果并根据语句类型显示
                    execution_logs = []
                    for result in results:
                        if result is None:
                            execution_logs.append("语句执行失败")
                            continue
                        stmt_type, stmt_result = result
                        if stmt_type == "select":
                            if stmt_result:  # 确保结果不为空
                                df = pd.DataFrame(stmt_result)
                                execution_logs.append(df)
                            else:
                                execution_logs.append("无查询结果")
                        else:
                            execution_logs.append(stmt_result)

                    # 显示执行结果
                    if execution_logs:
                        st.subheader("执行结果")
                        for i, log in enumerate(execution_logs):
                            if isinstance(log, pd.DataFrame):
                                st.dataframe(log)
                            else:
                                st.write(log)

                    st.success("SQL 执行成功！")

        except Exception as e:
            # 显示错误信息
            st.error(f"错误：{str(e)}")

with col2:
    # 显示数据库表状态
    update_tables_display()