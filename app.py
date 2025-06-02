import streamlit as st
from sql import Lexer, Parser, Executor
import pandas as pd
import json
from streamlit import code as st_code

# =================== 初始化数据库和状态管理 ===================
if "executor" not in st.session_state:
    st.session_state.executor = Executor()
if "tables_data" not in st.session_state:
    st.session_state.tables_data = {}
if "query_history" not in st.session_state:
    st.session_state.query_history = []
if "preview_sample" not in st.session_state:
    st.session_state.preview_sample = None
if "clear_flag" not in st.session_state:
    st.session_state.clear_flag = False

# =================== 预定义测试样例 ===================
SAMPLE_QUERIES = [
    {
        "name": "CREATE TABLE",
        "description": "创建用户表，订单表，产品表，商家表",
        "query": """
            CREATE TABLE users(id INT, name STRING, age INT);
            CREATE TABLE orders(id INT, user_id INT, product_id INT, merchant_id int, amount FLOAT, status STRING);
            CREATE TABLE products(id INT, name STRING, price FLOAT, stock INT);
            cReAte TABLE merchants(id INT, name STRING);
        """,
    },
    {
        "name": "INSERT",
        "description": "插入用户、订单、产品相关数据",
        "query": """
            INSERT INTO users VALUES (id = 1, name = 'Ali' + 'ce', age = 25);
            INSERT INTO users VALUES (id = 2, name = 'Bo' * 2, age = 30);
            INSERT INTO users VALUES (id = 3, name = 'Charlie', age = 22);
            INSERT INTO users VALUES (id = 4, name = 'David', age = 23);
            INSERT INTO orders (id, user_id, product_id, merchant_id, amount, status) VALUES (1, 1, 1,1, 100.5, 'paid');
            INSERT INTO orders VALUES (id = 2, user_id = 2, product_id =( 1 + 3 ) * 5 - 17, merchant_id = 2, amount = 200.75, status = 'pending');
            INSERT INTO orders VALUES (id = 3, user_id = 2 * 1, product_id = 1, merchant_id = 1,amount = 50.0 * 3, status = 'paid');
            INSERT INTO orders VALUES (id = 4, user_id = 3, product_id = 2, merchant_id = 2,amount = 75.25, status = 'pending');
            INSERT INTO orders VALUES (id = 5, user_id = 2, product_id = 2, merchant_id = 1,amount = 100, status = 'paid');
            INSERT INTO orders VALUES (id = 6, user_id = 3, product_id = 3, merchant_id = 2,amount = 25.0 * 3, status = 'paid');
            INSERT INTO orders VALUES (id = 7, user_id = 1, product_id = 1, merchant_id = 1,amount = 55, status = 'paid');
            INSERT INTO orders VALUES (id = 8, user_id = 1, product_id = 2,merchant_id = 2, amount = 599, status = 'paid');
            INSERT INTO orders VALUES (id = 9, user_id = 1, product_id = 3, merchant_id = 2,amount = 895, status = 'paid');
            INSERT INTO orders VALUES (id = 10, user_id = 3, product_id = 1, merchant_id = 2,amount = 55, status = 'paid');
            INSERT INTO orders VALUES (id = 11, user_id = 4, product_id = 1, merchant_id = 1,amount = 999, status = 'paid');
            INSERT INTO orders VALUES (id = 12, user_id = 4, product_id = 2, merchant_id = 1,amount = 699, status = 'paid');
            INSERT INTO orders VALUES (id = 13, user_id = 4, product_id = 3, merchant_id = 1,amount = 399, status = 'paid');
            INSERT INTO products VALUES (id = 1, name = 'Laptop', price = 999.99, stock = 10);
            INSERT INTO products VALUES (id = 2, name = 'Phone', price = 699.99, stock = 20);
            INSERT INTO products VALUES (id = 3, name = 'Tablet', price = 399.99, stock = 15);
            INSERT INTO merchants VALUES (id = 1, name = '联想');
            INSERT INTO merchants VALUES (id = 2, name = '苹果');
        """,
    },
    {
        "name": "SELECT",
        "description": "创建产品表，执行分组统计和条件查询",
        "query": """
            SELECT * FROM users;
            SELECT name, age FROM users WHERE age > 25;
            SELECT users.name, orders.amount, orders.status FROM users JOIN orders ON users.id == orders.user_id WHERE name == 'Alice';
            select users.name, products.name, orders.status FROM users JOIN orders ON users.id == orders.user_id JOIN products ON orders.product_id == products.id;
            select users.name, products.name, merchants.name, orders.amount from users JOIN orders ON users.id == orders.user_id JOIN products ON orders.product_id == products.id JOIN merchants ON orders.merchant_id == merchants.id orderby orders.amount desc;
            SELECT * FROM products orderby price desc limit 2 offset 1;
        """,
    },
    {
        "name": "DELETE",
        "description": "创建多表关联，执行复杂查询与聚合",
        "query": """
            DELETE FROM orders WHERE amount < 100 AND status == 'pending';
            DELETE FROM users WHERE id == 4;
        """,
    },
    {
        "name": "UPDATA",
        "description": "创建多表关联，执行复杂查询与聚合",
        "query": """
            UPDATE products SET stock = 5 WHERE id == 1;
        """,
    },
]


# =================== 数据库操作函数 ===================
def reset_tables_data():
    if hasattr(st.session_state.executor, "tables"):
        for table_name, table_info in st.session_state.executor.tables.items():
            columns = list(table_info["columns"].keys())
            data = table_info["data"]
            df = pd.DataFrame(data) if data else pd.DataFrame(columns=columns)
            st.session_state.tables_data[table_name] = df


def update_tables_display():
    reset_tables_data()
    if not st.session_state.tables_data:
        st.info("数据库为空，请创建表并插入数据。")
        return

    st.subheader("📊 数据库表结构", divider="grey")

    tab_list = list(st.session_state.tables_data.keys())
    tabs = st.tabs(tab_list)

    for i, table_name in enumerate(tab_list):
        with tabs[i]:
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"**表名**: `{table_name}`")

                if hasattr(st.session_state.executor, "tables"):
                    columns_info = st.session_state.executor.tables[table_name][
                        "columns"
                    ]
                    st.markdown("**表结构:**")
                    for col, dtype in columns_info.items():
                        st.markdown(f"- `{col}`: {dtype}")

                    row_count = len(
                        st.session_state.executor.tables[table_name]["data"]
                    )
                    st.markdown(f"**数据量:** {row_count} 行记录")

            with col2:
                df = st.session_state.tables_data[table_name]
                if df.empty:
                    st.info("表为空")
                else:
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"显示 {len(df)} 行数据")


# =================== 清空编辑器的回调函数 ===================
def clear_sql_editor():
    st.session_state.clear_flag = True
    return ""


# =================== 页面配置和标题 ===================
st.set_page_config(page_title="SQL 解释器", layout="wide", page_icon="🧮")
st.markdown(
    """
<style>
    .stButton > button {
        font-weight: 500 !important;
        border-radius: 8px !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 2.5rem;
        padding: 0.25rem 1rem;
        border-radius: 10px !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #2E86C1 !important;
        color: white !important;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div style="text-align:center">
    <h1 style='color:#2E86C1;font-size:2.5em;margin-bottom:5px'>🧮 SQL 解释器</h1>
    <p style='color:#616A6B;font-size:1.1em'>使用简易SQL引擎创建、查询和操作数据库表</p>
</div>
""",
    unsafe_allow_html=True,
)
st.header("", divider="rainbow")

# =================== 处理清空标志 ===================
if st.session_state.clear_flag:
    # 重置SQL输入，但不在session_state中保留
    sql_input_value = ""
    st.session_state.clear_flag = False
    st.rerun()
else:
    # 从session_state获取或初始化SQL输入
    sql_input_value = st.session_state.get("sql_input_value", "")

# =================== 测试样例预览页面 ===================
if st.session_state.preview_sample is not None:
    sample_idx = st.session_state.preview_sample
    sample = SAMPLE_QUERIES[sample_idx]

    st.subheader(f"🔍 SQL预览: {sample['name']}", divider="rainbow")
    st.caption(f"场景描述: {sample['description']}")

    # 完整显示SQL代码
    st.code(sample["query"], language="sql")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📥 加载到编辑器", use_container_width=True, type="primary"):
            st.session_state.sql_input_value = sample["query"].strip()
            st.session_state.preview_sample = None
            st.rerun()
    with col2:
        if st.button("← 返回主界面", use_container_width=True):
            st.session_state.preview_sample = None
            st.rerun()

    st.stop()  # 停止渲染其他内容

# =================== 主应用界面 ===================
# 侧边栏
with st.sidebar:
    st.subheader("🗃️ 数据库管理", divider="grey")

    if st.button("🔄 重置数据库", use_container_width=True, help="清除所有表和数据"):
        st.session_state.executor = Executor()
        st.session_state.tables_data = {}
        st.session_state.query_history = []
        st.session_state.preview_sample = None
        st.session_state.clear_flag = False
        st.success("✅ 数据库已重置")
        st.rerun()

    # 测试样例库
    st.subheader("🧪 测试样例库", divider="grey")
    st.caption("点击预览按钮查看详细SQL")

    for idx, sample in enumerate(SAMPLE_QUERIES):
        with st.container():
            col1, col2 = st.columns([2, 2])
            with col1:
                st.caption(f"📋 {sample['name']}")
            with col2:
                if st.button("预览", key=f"preview_{idx}", help="查看完整SQL"):
                    st.session_state.preview_sample = idx
                    st.rerun()

    # 查询历史记录
    st.subheader("📜 查询历史", divider="grey")
    if st.session_state.query_history:
        st.caption("点击刷新按钮重新执行查询")
        for idx, query in enumerate(reversed(st.session_state.query_history)):
            col1, col2 = st.columns([1, 8])
            with col1:
                refresh_btn = st.button("↻", key=f"run_{idx}", help="重新执行此查询")
            with col2:
                st.caption(
                    f"#{len(st.session_state.query_history)-idx} {query[:45]}{'...' if len(query) > 45 else ''}"
                )

            if refresh_btn:
                st.session_state.sql_input_value = query
                st.rerun()
    else:
        st.info("暂无查询历史")

    # 清除历史按钮
    if st.button("🗑️ 清除历史记录", use_container_width=True, type="secondary"):
        st.session_state.query_history = []
        st.success("✅ 历史记录已清除")
        st.rerun()

# 主编辑器区域
st.subheader("📝 SQL 编辑器", divider="grey")
st.caption(
    "💡 支持: CREATE TABLE, INSERT, SELECT, JOIN, WHERE, GROUP BY, HAVING 等SQL操作"
)
st.caption("💡 语法示例: INSERT INTO users VALUES (id=1, name='Alice', age=25)")

# 使用表单创建SQL编辑器
with st.form("sql_editor_form"):
    sql_input = st.text_area(
        "SQL输入",
        height=300,
        value=sql_input_value,
        placeholder="输入SQL语句（多条语句用分号分隔）...\n例如：\nCREATE TABLE users(id INT, name STRING);\nINSERT INTO users VALUES (id=1, name='Alice');\nSELECT * FROM users;",
        key="sql_input_area",
    )

    # 操作按钮在表单中
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        execute_btn = st.form_submit_button(
            "▶️ 执行", type="primary", use_container_width=True
        )

    with col2:
        # 清空按钮通过回调函数处理
        clear_btn = st.form_submit_button(
            "🗑️ 清空", use_container_width=True, help="清空SQL编辑器内容"
        )

# 处理清空按钮
if clear_btn:
    st.session_state.clear_flag = True
    st.session_state.sql_input_value = ""  # 同时清空保存的值
    st.rerun()

# 处理执行按钮
if execute_btn:
    # 保存当前SQL输入值
    st.session_state.sql_input_value = sql_input

    try:
        if not sql_input.strip():
            st.warning("⚠️ 请输入有效的SQL语句")
        else:
            # 保存到历史（避免重复）
            if (
                not st.session_state.query_history
                or st.session_state.query_history[-1] != sql_input.strip()
            ):
                st.session_state.query_history.append(sql_input.strip())
                if len(st.session_state.query_history) > 20:
                    st.session_state.query_history.pop(0)

            # 词法分析
            lexer = Lexer(sql_input)
            tokens = lexer.tokenize()

            # 语法分析
            parser = Parser(tokens)
            ast = parser.parse_program()

            # 执行SQL
            results = st.session_state.executor.run(ast)
            reset_tables_data()  # 更新表数据

            # =================== 使用标签页展示结果 ===================
            if results:
                st.subheader("🧾 执行结果", divider="grey")

                # 创建标签页用于多结果展示
                result_tabs = st.tabs([f"结果 {i+1}" for i in range(len(results))])

                for i, result in enumerate(results):
                    with result_tabs[i]:
                        stmt_type, stmt_result = result

                        # 针对不同类型结果显示不同内容
                        if stmt_type == "select":
                            if stmt_result:
                                df = pd.DataFrame(stmt_result)
                                st.dataframe(df, use_container_width=True)
                                st.success(f"✅ 查询成功，返回 {len(df)} 行记录")
                            else:
                                st.info("❌ 没有查询结果")
                        else:
                            st.success(f"✅ {stmt_type.upper()} 语句执行成功")
                            st.code(stmt_result, language="sql")

            st.success("✅ SQL执行成功！")
            st.balloons()
    except Exception as e:
        st.error(f"🚨 执行错误：{str(e)}")
        st.error(
            "常见错误原因：\n1. 表名错误或不存在\n2. 列名拼写错误\n3. 数据类型不匹配\n4. SQL语法错误"
        )

# 数据库表展示
if "tables_data" not in st.session_state or not st.session_state.tables_data:
    reset_tables_data()
update_tables_display()
