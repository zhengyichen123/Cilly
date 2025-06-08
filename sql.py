import re
from collections import defaultdict


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
        "SET": "SET",
        "DEFAULT": "DEFAULT",
        "ALL": "ALL",
        "UNION": "UNION",
        "DISTINCT": "DISTINCT",
        "ORDERBY": "ORDERBY",
        "DESC": "DESC",
        "ASC": "ASC",
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
        # 聚合函数
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
        ("FLOAT", r"\d+\.(\d*)?"),  # 浮点数
        ("INT", r"\d+"),  # 整数
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
                    if token_type == "FLOAT":
                        val = float(val)
                    if token_type == "INT":
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

    def field_access(self, left, bp=0):
        self.expect("DOT")
        right = self.expect(["ID"])
        return ["field", left[1], right.value]

    op2 = {
        "DOT": (90, 91, field_access),
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

        SELECT [DISTINCT] select_list
        FROM table_source
        [WHERE row_filter]
        [GROUP BY grouping_condition]
        [HAVING group_filter]
        [ORDER BY sort_expression]
        [LIMIT limit_count]
        [OFFSET offset_count];

        在使用 GROUP BY 分组查询时, SELECT 子句中除了用于分组的字段外，其他字段必须通过 聚合函数（如 MAX, MIN, AVG, COUNT, SUM 等） 来提取数据, HAVING 也如此。
        """
        self.expect(["SELECT"])
        fields = []
        while self.peek() and self.peek().type != "FROM":
            table = self.expect(["ID", "MUL"]).value
            field = None
            if self.peek() and self.peek().type == "DOT":
                self.advance()
                field = self.expect(["ID"]).value

            if field is None:
                # [table, colomn]
                fields.append(["field", field, table])
            else:
                fields.append(["field", table, field])

            if self.peek() and self.peek().type == "COMMA":
                self.advance()

        self.expect(["FROM"])
        table_name = self.expect(["ID"]).value

        for field in fields:
            if field[1] is None:
                fields[fields.index(field)] = ["field", table_name, field[2]]

        joins = []
        while self.peek() and self.peek().type == "JOIN":
            self.advance()
            table = self.expect(["ID"]).value
            self.expect(["ON"])
            cond = self.parse_expr()
            joins.append([table, cond])

        condition = None
        if self.peek() and self.peek().type == "WHERE":
            self.advance()
            condition = self.parse_expr()

        groups = None
        if self.peek() and self.peek().type == "GROUPBY":
            groups = []
            self.advance()
            depend = []
            while self.peek() and self.peek().type == "ID":
                depend.append(self.parse_expr())
                if self.peek() and self.peek().type == "COMMA":
                    self.advance()
            #  GROUP BY 后无 ID 直接报错
            if len(depend) == 0:
                self.expect(["ID"])

            cond = None
            if self.peek() and self.peek().type == "HAVING":
                self.advance()
                cond = self.parse_expr()

            groups.append(depend)
            groups.append(cond)

        sort = None
        if self.peek() and self.peek().type == "ORDERBY":
            self.advance()
            id = self.parse_expr()

            if self.peek() and self.peek().type == "DESC":
                self.advance()
                sort = [id, "DESC"]
            else:
                self.advance()
                sort = [id, "ASC"]

        limit = None
        if self.peek() and self.peek().type == "LIMIT":
            self.advance()
            limit = self.expect(["INT"]).value

        offset = 0
        if self.peek() and self.peek().type == "OFFSET":
            self.advance()
            offset = self.expect(["INT"]).value

        self.expect(["SEMICOLON"])
        return [
            "select",
            table_name,
            fields,
            joins,
            condition,
            groups,
            sort,
            limit,
            offset,
        ]

    def parse_update(self):

        self.expect(["UPDATE"])
        table_name = self.expect(["ID"]).value
        self.expect(["SET"])

        fields = []
        while (
            self.peek()
            and self.peek().type != "WHERE"
            and self.peek().type != "SEMICOLON"
        ):
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
        self.cur_table = None

    def execute(self, ast):
        """执行 AST 的入口函数"""
        results = []
        if ast[0] == "program":
            for stmt in ast[1]:
                result = self.execute_stmt(stmt)
                results.append(result)
        else:
            result = self.execute_stmt(ast)
            results.append(result)
        return results

    def execute_stmt(self, stmt):
        """执行单个语句"""
        stmt_type = stmt[0]
        if stmt_type == "create":
            table_name = stmt[1]
            columns = stmt[2]
            self.tables[table_name] = {
                "columns": {col[0]: col[1] for col in columns},
                "data": [],
            }
            """
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
            """
            print(f"表 `{table_name}` 创建成功，列: {columns}")
            return ("create", f"表 `{table_name}` 创建成功，列: {columns}")
        elif stmt_type == "insert":
            table_name = stmt[1]
            fields = stmt[2]  # 操作域
            values = stmt[3]
            row = {}
            for field, value in values:
                row[field] = self.eval_expr(value)  # 计算表达式的值
            self.tables[table_name]["data"].append(row)
            print(f"插入到 `{table_name}`: {row}")
            return ("insert", f"插入到 `{table_name}`: {row}")

        elif stmt_type == "update":
            table_name = stmt[1]
            updates = stmt[2]
            condition = stmt[3]

            self.cur_table = table_name

            if table_name not in self.tables:
                print(f"表 `{table_name}` 不存在")
                return ("update", f"表 `{table_name}` 不存在")

            update_count = 0

            for row in self.tables[table_name]["data"]:
                if condition is None or self.eval_condition(
                    condition, {f"{table_name}.{k}": v for k, v in row.items()}
                ):
                    for field, expr in updates:
                        row[field] = self.eval_expr(expr)
                    update_count += 1

            print(f"更新了{table_name}的{update_count}行")
            return ("update", f"更新了 `{table_name}` 的 {update_count} 行")

        elif stmt_type == "delete":
            table_name = stmt[1]
            condition = stmt[2]
            if table_name not in self.tables:
                print(f"表 `{table_name}` 不存在")
                return ("delete", f"表 `{table_name}` 不存在")
            if condition is None:
                count = len(self.tables[table_name]["data"])
                self.tables[table_name]["data"] = []
                print(f"清空 `{table_name}` 的 {count} 行")
                return ("delete", f"清空 `{table_name}` 的 {count} 行")
            else:

                self.cur_table = table_name

                original_data = self.tables[table_name]["data"]
                self.tables[table_name]["data"] = [
                    row
                    for row in original_data
                    if not self.eval_condition(
                        condition, {f"{table_name}.{k}": v for k, v in row.items()}
                    )
                ]
                deleted_count = len(original_data) - len(
                    self.tables[table_name]["data"]
                )
                print(f"从 `{table_name}` 删除 {deleted_count} 行")
                return ("delete", f"从 `{table_name}` 删除 {deleted_count} 行")

        elif stmt_type == "select":
            table_name = stmt[1]  # 主表名字
            fields = stmt[2]  # list[0] = [table, colomn]
            joins = stmt[3]
            condition = stmt[4]
            groups = stmt[5]
            sort = stmt[6]
            limit = stmt[7]
            offset = stmt[8]

            self.cur_table = table_name

            if table_name not in self.tables:
                print(f"表 `{table_name}` 不存在")
                return ("select", f"表 `{table_name}` 不存在")

            join_result = None

            if len(joins) > 0:
                join_result = []
                main_table = [
                    {f"{table_name}.{key}": value for key, value in row.items()}
                    for row in self.tables[table_name]["data"]
                ]
                for join in joins:
                    if join[0] not in self.tables:
                        print(f"表 `{join[0]}` 不存在")
                        return []
                    join_table = [
                        {f"{join[0]}.{key}": value for key, value in row.items()}
                        for row in self.tables[join[0]]["data"]
                    ]
                    temp = []
                    for main_data in main_table:
                        for join_data in join_table:
                            main_data.update(join_data)
                            temp.append(main_data.copy())

                    for row in temp:
                        if join[1] is None or self.eval_condition(join[1], row):
                            join_result.append(row)

                    main_table = join_result
                    join_result = []

                join_result = main_table

            if join_result is None:
                join_result = [
                    {f"{table_name}.{key}": value for key, value in row.items()}
                    for row in self.tables[table_name]["data"]
                ]

            result = [] # where之后的结果
            for row in join_result:
                if condition is None or self.eval_condition(condition, row):
                    result.append(row)

            # groups : [depend, cond] depend是分组字段[ID, field]
            if groups is not None:

                group_keys = groups[0]
                having_cond = groups[1]

                grouped_data = defaultdict(list)

                for row in result:
                    group_key = tuple(row.get(self.eval_expr(key)[1]) for key in group_keys)
                    grouped_data[group_key].append(row)

                aggregated_result = []
                for key, rows in grouped_data.items():
                    if isinstance(key, tuple):
                        group_dict = {self.eval_expr(k)[1]: v for k, v in zip(group_keys, key)}
                    else:
                        group_dict = {self.eval_expr(group_keys[0])[1]: key}

                    # group_dict = {name : alice, age : 20}
                    agg_row = {}
                    agg_row.update(group_dict)

                    for field in fields:
                        expr = field  # ["field", table, column]
                        if expr[2] in ["COUNT", "SUM", "AVG", "MIN", "MAX"]:
                            col_name = self.eval_expr(expr[2])
                            func_name = expr[2]  # COUNT / SUM / AVG / MIN / MAX

                            values = [row.get(col_name) for row in rows if col_name in row]

                            if func_name == "COUNT":
                                agg_row[col_name] = len(values)
                            elif func_name == "SUM":
                                agg_row[col_name] = sum(values)
                            elif func_name == "AVG":
                                agg_row[col_name] = sum(values) / len(values) if values else None
                            elif func_name == "MIN":
                                agg_row[col_name] = min(values) if values else None
                            elif func_name == "MAX":
                                agg_row[col_name] = max(values) if values else None
                        else:
                            # 非聚合字段必须是 GROUP BY 的字段，否则应报错（SQL 规范）
                            agg_row[expr[2]] = group_dict.get(expr[2])

                    # Step 4: 应用 HAVING 条件
                    # 聚合函数字段必须先取别名，然后才能应用 HAVING, ORDERBY 条件
                    if having_cond is None or self.eval_condition(having_cond, agg_row):
                        aggregated_result.append(agg_row)

                result = aggregated_result
                pass

            if sort is not None:
                field = sort[0]
                field = self.eval_expr(field)
                if field[1] not in result[0].keys():
                    raise Exception("排序字段不存在")

                sort_way = sort[1]
                result = sorted(
                    result, key=lambda x: x.get(field[1]), reverse=(sort_way == "DESC")
                )

            if offset is not None and offset < 0:
                raise ValueError("偏移量不能为负数")
            if limit is not None and limit <= 0:
                raise ValueError("限制数必须大于0")

            all = False
            if limit is None:
                all = True

            final_result = []

            if not all:
                if offset + limit <= len(result):
                    final_result = result[offset : offset + limit] 
                else:
                    raise ValueError("请求范围超过结果范围")
            else:
                if offset < len(result):
                    final_result = result[offset:]
                else:
                    raise ValueError("请求范围超过结果范围")

            selected_fields = []

            all = False
            for field in fields:
                if field[2] == "*":
                    all = True
                    break

            if all == False:
                selected_fields = [self.eval_expr(field)[1] for field in fields]
                final_result = [
                    {field: row[field] for field in selected_fields}
                    for row in final_result
                ]

            print(
                f"查询 `{table_name}` 的结果(从第{offset}条开始显示{len(final_result)}条记录，共{len(result)}条): {final_result}"
            )
            return ("select", final_result)

    def eval_expr(self, expr, row):
        # 算术表达式
        if expr[0] == "INT":
            return expr[1]
        elif expr[0] == "FLOAT":
            return expr[1]
        elif expr[0] == "STRING":
            return expr[1]  # 字符串直接返回
        elif expr[0] in ["TRUE", "FALSE"]:
            return expr[0] == "TRUE"  # 布尔值转换
        elif expr[0] == "ID":
            return [
                "ID",
                f"{self.cur_table}.{expr[1]}",
            ]  # ID 返回名称，实际值在条件中处理
        elif expr[0] == "unary":
            return -expr[2]

        elif expr[0] == "field":
            return ["ID", f"{expr[1]}.{expr[2]}"]  # [table, colomn]

        elif expr[0] == "binary":
            left = self.eval_expr(expr[2])
            right = self.eval_expr(expr[3])
            op = expr[1]
            if op == "+":
                if type(left) != type(right):
                    raise TypeError(f"不支持的 + 运算: {type(left)} 和 {type(right)}")

                return left + right

            elif op == "-":

                if isinstance(left, int) and isinstance(right, int):
                    return left - right

                raise TypeError(f"不支持的 - 运算: {type(left)} 和 {type(right)}")

            elif op == "*":

                if isinstance(left, str) and isinstance(right, str):
                    raise TypeError(f"不支持的 * 运算: {type(left)} 和 {type(right)}")

                return left * right

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
        # 逻辑表达式
        if condition[0] == "binary":
            op = condition[1]
            left = condition[2]
            right = condition[3]

            left_val = self.eval_expr(left)
            if isinstance(left_val, list):
                name = left_val[1]
                left_val = row.get(name)
                if left_val is None:
                    raise ValueError(f"找不到{name} 字段")

            right_val = self.eval_expr(right)
            if isinstance(right_val, list):
                name = right_val[1]
                right_val = row.get(name)
                if right_val is None:
                    raise ValueError(f"找不到{name} 字段")

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

            elif op == "and":
                return self.eval_condition(left, row) and self.eval_condition(
                    right, row
                )

            elif op == "or":
                return self.eval_condition(left, row) or self.eval_condition(right, row)

        elif condition[0] == "unary":
            op = condition[1]
            expr = condition[2]
            if op == "NOT":
                return not self.eval_condition(expr, row)

        return False

    def run(self, ast):
        """运行整个程序"""
        return self.execute(ast)




if __name__ == "__main__":

    sql1 = """
        CREATE TABLE users(id INT, name STRING, age INT);
        CREATE TABLE orders(id INT, user_id INT, product_id INT, merchant_id int, amount FLOAT, status STRING);
        CREATE TABLE products(id INT, name STRING, price FLOAT, stock INT);
        cReAte TABLE merchants(id INT, name STRING);
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
        SELECT * FROM users;
        SELECT name, age FROM users WHERE age > 25;
        SELECT users.name, orders.amount, orders.status FROM users JOIN orders ON users.id == orders.user_id WHERE name == 'Alice';
        select users.name, products.name, orders.status FROM users JOIN orders ON users.id == orders.user_id JOIN products ON orders.product_id == products.id;
        select users.name, products.name, merchants.name, orders.amount from users JOIN orders ON users.id == orders.user_id JOIN products ON orders.product_id == products.id JOIN merchants ON orders.merchant_id == merchants.id orderby orders.amount desc;
        SELECT * FROM products orderby price desc limit 2 offset 1;
        DELETE FROM orders WHERE amount < 100 AND status == 'pending';
        DELETE FROM users WHERE id == 4;
        UPDATE products SET stock = 5 WHERE id == 1;
    """
    sql_commands = """
    SELECT name course.score from student JOIN course ON student.id == course.id where student.id >= 2 and id <= 5 LIMIT 2 OFFSET 1;
    """

    lexer = Lexer(sql1)
    tokens = lexer.tokenize()
    print(f"token :  \n{tokens}")
    parser = Parser(tokens)
    ast = parser.parse_program()
    print(f"ast : \n{ast}")
    executor = Executor()
    result = executor.run(ast)
