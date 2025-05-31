import re

"""
1. 子查询
2. JOIN查询 INNER JOIN, LEFT JOIN, RIGHT JOIN
3. 聚合函数 COUNT() SUM() AVG() MAX() MIN()
4. ORDER BY / LIMIT / OFFSET /GROUP BY
5. UPDATE, ALTER语句
6. 自定义函数与函数调用
7. 多表和嵌套表达式
"""

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def get(self):
        return [self.type, self.value]

    def __repr__(self):
        return f"[{self.type}, {self.value}]"


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0

    KEYWORDS = {
        "CREATE": "CREATE",
        "TABLE": "TABLE",
        "INSERT": "INSERT",
        "INTO": "INTO",
        "VALUE": "VALUE",
        "VALUES": "VALUES",
        "DELETE": "DELETE",
        "FROM": "FROM",
        "WHERE": "WHERE",
        "SELECT": "SELECT",
        "UPDATE": "UPDATE",
        "SET" : "SET",
        "DEFAULT": "DEFAULT",
        "ALL": "ALL",
        "UNION": "UNION",
        "DISTINCT": "DISTINCT",
        "ORDERBY": "ORDERBY",
        "GROUPBY": "GROUPBY",
        "HAVING": "HAVING",
        "LIMIT": "LIMIT",
        "OFFSET": "OFFSET",
        "AS": "AS",
        "INNER": "INNER",
        "JOIN": "JOIN",
        "LEFT": "LEFT",
        "RIGHT": "RIGHT",
        "ON": "ON",
        "USING": "USING",
        # 内置函数
        "AVG": "AVG",
        "SUM": "SUM",
        "COUNT": "COUNT",
        "MAX": "MAX",
        "MIN": "MIN",
        # 基本数据类型
        "INT": "DTYPE",
        "STRING": "DTYPE",
        "FLOAT": "DTYPE",
        "BOOLEAN": "DTYPE",
        # 逻辑运算符
        "AND": "AND",
        "OR": "OR",
        "NOT": "NOT",
        "TRUE": "TRUE",
        "FALSE": "FALSE",
        "UNKNOWN": "UNKNOWN",
    }

    TOKEN_SPEC = [
        ("ID", r"[A-Za-z_][A-Za-z0-9_]*"),  # 标识符
        ("FLOAT", r"\d+\.(\d*)?"), # 浮点数
        ("INT", r"\d+"), # 整数
        ("STRING", r"'[^']*'"),  # 字符串
        ("DOT", r"\."),  # 点 .
        # 条件运算符
        ("EQ", r"=="),  # 等于 ==
        ("NEQ", r"!="),  # 不等于 !=
        ("LTE", r"<="),  # 小于等于 <=
        ("GTE", r">="),  # 大于等于 >=
        ("LT", r"<"),  # 小于 <
        ("GT", r">"),  # 大于 >
        ("ASSIGN", r"="),  # 赋值 =
        # 基本运算符
        ("PLUS", r"\+"),  # 加号 +
        ("MINUS", r"\-"),  # 减号 -
        ("MUL", r"\*"),  # 乘号 *
        ("DIV", r"/"),  # 除号 /
        # 分隔符
        ("COMMA", r","),  # 逗号 ,
        ("LPAREN", r"\("),  # 左括号 (
        ("RPAREN", r"\)"),  # 右括号 )
        ("WS", r"\s+"),  # 空白字符
        ("SEMICOLON", r";"),  # 分号
    ]

    def tokenize(self):
        tokens = []
        while self.pos < len(self.text):
            match = None
            for token_type, regex in self.TOKEN_SPEC:
                pattern = re.compile(regex)
                match = pattern.match(self.text, self.pos)
                if match:
                    val = match.group(0)
                    if token_type == 'FLOAT':
                        val = float(val)
                    if token_type == 'INT':
                        val = int(val)

                    if token_type == "WS":
                        self.pos = match.end()
                        break
                    elif token_type == "ID" and val.upper() in self.KEYWORDS:
                        token_type = self.KEYWORDS[val.upper()]
                        val = val.lower()
                    if token_type == "STRING":
                        val = val[1:-1]  # remove quotes
                    tokens.append(Token(token_type, val))
                    self.pos = match.end()
                    break
            if not match:
                raise SyntaxError(
                    f"Lexer: 非法字符'{self.text[self.pos]}'位于 {self.pos}"
                )
        return tokens


class Parser:
    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pred_anal_table = {}
        self.curpos = 0
        self.prevpos = 0

    def peek(self):
        if self.curpos < len(self.tokens):
            return self.tokens[self.curpos]
        return None

    def advance(self):
        self.curpos += 1

    def mark(self):
        self.prevpos = self.curpos

    def backroll(self):
        self.curpos = self.prevpos

    def expect(self, token_type: list):
        token = self.peek()
        if token and token.type in token_type:
            self.advance()
            return token
        else:
            raise SyntaxError(f"Parser: 期望 {token_type}, 得到 {token}")

    def literal(self, bp: int):
        token = self.peek()
        self.advance()
        return token.get()

    def unary(self, bp: int):
        op = self.peek().value
        self.advance()
        expr = self.parse_expr(bp)
        return ["unary", op, expr]

    def parens(self, bp=0):
        self.expect("LPAREN")
        expr = self.parse_expr()
        self.expect("RPAREN")
        return expr

    op1 = {
        "ID": (100, literal),
        "FLOAT": (100, literal),
        "INT": (100, literal),
        "STRING": (100, literal),
        "TRUE": (100, literal),
        "FALSE": (100, literal),
        "MINUS": (85, unary),
        "NOT": (85, unary),
        "LPAREN": (100, parens),
    }

    def get_op1_parser(self, t: str):
        if t not in self.op1:
            raise SyntaxError(f"Parser: 错误token {t}")
        return self.op1[t]

    def binary(self, left, bp: int):
        op = self.peek().value
        self.advance()
        right = self.parse_expr(bp)
        return ["binary", op, left, right]

    op2 = {
        "MUL": (80, 81, binary),
        "DIV": (80, 81, binary),
        "PLUS": (70, 71, binary),
        "MINUS": (70, 71, binary),
        "GT": (60, 61, binary),
        "GTE": (60, 61, binary),
        "LT": (60, 61, binary),
        "LTE": (60, 61, binary),
        "EQ": (50, 51, binary),
        "NEQ": (50, 51, binary),
        "AND": (40, 41, binary),
        "OR": (30, 31, binary),
    }

    def get_op2_parser(self, t: str):
        if t not in self.op2:
            return (0, 0, None)
        else:
            return self.op2[t]

    # 解析表达式：主要是条件判断，数字运算和字符串拼接
    # 末尾自动跳到下一个token
    def parse_expr(self, bp=0):
        r_bp, parser = self.get_op1_parser(self.peek().type)
        left = parser(self, r_bp)

        while True:
            l_bp, r_bp, parser = self.get_op2_parser(self.peek().type)
            if parser == None or l_bp <= bp:
                break
            left = parser(self, left, r_bp)

        return left

    def parse_insert(self):
        """
        1. insert into user (id, name) values (1, 'test');
        2. insert into user values (id = 1, name = 'test');
        3. insert into user values (id = 1 + 10 * 2, name = 'A' + 'lice');
        4. insert into user values (id = table.id + 10, name = table.name + 'else');
        5. 支持对于某表函数
        """
        self.expect(["INSERT"])
        self.expect(["INTO"])
        table = self.expect(["ID"]).value

        # 可选字段列表
        fields = []
        if self.peek() and self.peek().type == "LPAREN":
            self.expect(["LPAREN"])
            while self.peek().type != "RPAREN":
                field = self.expect(["ID"]).value
                fields.append(field)
                if self.peek() and self.peek().type == "COMMA":
                    self.advance()
            self.expect(["RPAREN"])

        self.expect(["VALUES"])
        self.expect(["LPAREN"])

        values = []

        if self.peek().type == "ID":
            while self.peek().type != "RPAREN":
                if self.peek().value not in fields:
                    fields.append(self.peek().value)
                id = self.expect(["ID"]).value
                self.expect(["ASSIGN"])
                values.append([id, self.parse_expr()])
                if self.peek() and self.peek().type == "COMMA":
                    self.advance()
        else:
            if fields is None:
                raise SyntaxError(f"Parser: 无法识别字段: {self.peek().value}")
            for i in range(len(fields)):
                values.append([fields[i], self.parse_expr()])
                if self.peek() and self.peek().type == "COMMA":
                    self.advance()

        self.expect(["RPAREN"])
        self.expect(["SEMICOLON"])

        return ["insert", table, fields, values]

    def parse_delete(self):
        """
        1. delete from user where id == 1;
        2. delete from user where id > 1;
        3. delete from user where id > 1 and name = 'test';
        4. delete from user where id > 1 or name = 'test';
        5. delete from user where id > 1 and name = 'test' or age < 18;
        6. delete from user where id > 1 and (name = 'test' or age < 18);
        7. delete from user where id in (select user_id from orders);
        8. delete from user;
        """
        self.expect(["DELETE"])
        self.expect(["FROM"])
        table = self.expect(["ID"]).value

        condition = None
        if self.peek() and self.peek().type == "WHERE":
            self.expect(["WHERE"])
            condition = self.parse_expr()

        self.expect(["SEMICOLON"])
        return ["delete", table, condition]

    def parse_create(self):
        """
        1. create table user (id int, name string);
        2. 默认值, UNIQUE
        """
        self.expect(["CREATE"])
        self.expect(["TABLE"])
        table_name = self.expect(["ID"]).value
        self.expect(["LPAREN"])

        columns = []

        while self.peek() and self.peek().type != "RPAREN":
            col_name = self.expect(["ID"]).value
            col_type = self.expect(["DTYPE"]).value

            columns.append([col_name, col_type])
            if self.peek() and self.peek().type == "COMMA":
                self.advance()

        self.expect(["RPAREN"])
        self.expect(["SEMICOLON"])
        return ["create", table_name, columns]

    def parse_select(self):
        """
        1. SELECT id, name FROM users WHERE id == 1;
        2. SELECT * FROM users WHERE age > 18 AND status == 'active';
        3. SELECT * FROM users u JOIN orders o ON u.id == o.user_id;
        4. SELECT * FROM users ORDER BY id DESC LIMIT 10 OFFSET 5;
        """
        self.expect(["SELECT"])
        fields = []
        while self.peek().type != "FROM":
            fields.append(self.expect(["ID", "MUL"]).value)
            if self.peek() and self.peek().type == "COMMA":
                self.advance()

        self.expect(["FROM"])

        table_name = self.expect(["ID"]).value

        condition = None

        if self.peek() and self.peek().type == "WHERE":
            self.advance()
            condition = self.parse_expr()

        self.expect(["SEMICOLON"])
        return ["select", table_name, fields, condition]

    def parse_update(self):

        self.expect(["UPDATE"])
        table_name = self.expect(["ID"]).value
        self.expect(["SET"])

        fields = []
        while self.peek() and self.peek().type != "WHERE" and self.peek().type != "SEMICOLON":
            field = []
            field.append(self.expect(["ID"]).value)
            self.expect(["ASSIGN"])
            field.append(self.parse_expr())
            fields.append(field)
            if self.peek() and self.peek().type == "COMMA":
                self.advance()

        condition = None
        if self.peek() and self.peek().type == "WHERE":
            self.advance()
            condition = self.parse_expr()
        
        self.expect(["SEMICOLON"])
        return ["update", table_name, fields, condition]

    def parse_statement(self):
        token = self.peek()
        if token.type == "INSERT":
            return self.parse_insert()
        elif token.type == "DELETE":
            return self.parse_delete()
        elif token.type == "CREATE":
            return self.parse_create()
        elif token.type == "SELECT":
            return self.parse_select()
        elif token.type == "UPDATE":
            return self.parse_update()
        else:
            raise SyntaxError(f"非法token: {token}")

    def parse_program(self):
        statements = []
        while self.peek() is not None:
            stmt = self.parse_statement()
            statements.append(stmt)
        return ["program", statements]


class Executor:
    """
    ["program", statements]
    ["create", table_name, fields]
    ["insert", table_name, fields, values]
    ["select", table_name, fields, condition]
    ["delete", table_name, condition]
    """

    def __init__(self):
        self.tables = {}

    def execute(self, ast):
        """执行 AST 的入口函数"""
        if ast[0] == "program":
            for stmt in ast[1]:
                self.execute_stmt(stmt)
        else:
            self.execute_stmt(ast)

    def execute_stmt(self, stmt):
        """执行单个语句"""
        stmt_type = stmt[0]
        if stmt_type == "create":
            table_name = stmt[1]
            columns = stmt[2]
            self.tables[table_name] = {"columns": {col[0]: col[1] for col in columns}, "data": []}
            '''
            本数据库结构
            self.tables = {

                # user table
                "user": {
                    "columns": {
                        "id": "int"
                        "name":"string"
                    }
                    "data":[
                        {}
                        {}
                    ]
                }

                #(other tables)
            } 
            '''
            print(f"表 `{table_name}` 创建成功，列: {columns}")
        elif stmt_type == "insert":
            table_name = stmt[1]
            fields = stmt[2] # 操作域
            values = stmt[3]
            row = {}
            for field, value in zip(fields, values):
                row[field] = self.eval_expr(value[1])  # 计算表达式的值
            self.tables[table_name]["data"].append(row)
            print(f"插入到 `{table_name}`: {row}")
        elif stmt_type == "delete":
            table_name = stmt[1]
            condition = stmt[2]
            if condition is None:
                count = len(self.tables[table_name]["data"])
                self.tables[table_name]["data"] = []
                print(f"清空 `{table_name}` 的 {count} 行")
            else:
                original_data = self.tables[table_name]["data"]
                self.tables[table_name]["data"] = [
                    row for row in original_data if not self.eval_condition(condition, row)
                ]
                deleted_count = len(original_data) - len(self.tables[table_name]["data"])
                print(f"从 `{table_name}` 删除 {deleted_count} 行")
        elif stmt_type == "select":
            table_name = stmt[1]
            fields = stmt[2]
            condition = stmt[3]
            if table_name not in self.tables:
                print(f"表 `{table_name}` 不存在")
                return []
            result = []
            for row in self.tables[table_name]["data"]:
                if condition is None or self.eval_condition(condition, row):
                    if fields == ['*']:
                        selected = row
                    else:
                        selected = {field: row.get(field) for field in fields}
                    result.append(selected)
            print(f"查询 `{table_name}` 的结果: {result}")
            return result

    def eval_expr(self, expr):
        """评估表达式，支持数字运算和字符串操作"""
        if expr[0] == "INT":
            return expr[1]  
        elif expr[0] == "FLOAT":
            return expr[1]
        elif expr[0] == "STRING":
            return expr[1]  # 字符串直接返回
        elif expr[0] in ["TRUE", "FALSE"]:
            return expr[0] == "TRUE"  # 布尔值转换
        elif expr[0] == "ID":
            return expr[1]  # ID 返回名称，实际值在条件中处理
        elif expr[0] == "binary":
            left = self.eval_expr(expr[2])
            right = self.eval_expr(expr[3])
            op = expr[1]
            if op == "+":
                return left + right 
            
            elif op == "-":
                return left - right

            elif op == "*": 
                return left * right  # 数字相乘   
            
            elif op == "/":
                if isinstance(left, int) and isinstance(right, int):
                    if right == 0:
                        raise ZeroDivisionError("除数不能为0！")
                    else:
                        return left / right
                else:
                    raise TypeError(f"不支持的 / 运算: {type(left)} 和 {type(right)}")            

        return None

    def eval_condition(self, condition, row):
        """评估条件表达式"""
        if condition[0] == "binary":
            op = condition[1]
            left = condition[2]
            right = condition[3]
            if left[0] == "ID":
                left_val = row.get(left[1])  # 从行中获取字段值
            else:
                left_val = self.eval_expr(left)
            right_val = self.eval_expr(right)
            if op == "==":
                return left_val == right_val
            elif op == ">":
                return left_val > right_val
            elif op == "<":
                return left_val < right_val
            elif op == ">=":
                return left_val >= right_val
            elif op == "<=":
                return left_val <= right_val
            elif op == "!=":
                return left_val != right_val
        
            elif op == "AND":
                return self.eval_condition(left, row) and self.eval_condition(right, row)
            
            elif op == "OR":
                return self.eval_condition(left, row) or self.eval_condition(right, row)

        return False

    def run(self, ast):
        """运行整个程序"""
        self.execute(ast)


# def run_sql(sql, executor):
#     lexer = Lexer(sql)
#     tokens = lexer.tokenize()
#     parser = Parser(tokens)
#     ast = parser.parse()
#     return executor.execute(ast)


if __name__ == "__main__":

    sql1 = """
    CREATE TABLE users(id INT, name String);
    INSERT INTO users VALUES (id = (1 + 1) * 3, name = 'Alice');
    INSERT INTO users VALUES (id = 2, name = 'Bob');
    SELECT * FROM users;
    DELETE FROM users WHERE id == 2;
    SELECT id, name FROM users WHERE id == 4;
    """
    sql_commands = """
    update users set name = 'Alice' where id >= 1 and name == 'Bob';
    """
    lexer = Lexer(sql_commands)
    tokens = lexer.tokenize()
    print(f"token :  \n{tokens}")
    parser = Parser(tokens)
    ast = parser.parse_program()
    print(f"ast : \n{ast}")
    executor = Executor()
    # result = executor.run(ast)
