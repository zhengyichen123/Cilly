"""
cilly 语法

program : statement* EOF

statement
    : define_statement
    | assign_statement
    | print_statement
    | if_statement
    | while_statement
    | continue_statement
    | break_statement
    | return_statement
    | block_statement
    | expr_statement
    ;

define_statement
    : 'var' ID '=' expr ';'
    ;

assign_statement
    : ID '=' expr ';'
    ;

print_statement
    : 'print' '(' args? ')' ';'
    ;

args : expr (',' expr)* ;

if_statement
    : 'if' '(' expr ')' statement ('else' statement)?
    ;

while_statement
    : 'while' '(' expr ')' statement
    ;

continue_statement
    : 'continue' ';'
    ;

break_statement
    : 'break' ';'
    ;

return_statement
    : 'return' expr? ';'
    ;

block_statement
    : '{' statement* '}'
    ;

expr_statement:
    : expr ';'

expr
    : id | num | string | 'true' | 'false' | 'null'
    | '(' expr ')'
    | ('-' | '!') expr
    | expr ('+' | '-' | '*' | '/' | '==' | '!=' | '>' | '>=' | '<' | '<=' | '&&' | '||') expr
    | 'fun' '(' params? ')' block_statement
    | expr '(' args? ')'
    ;

表达式实现
方法1：改造文法

expr: logic_expr
logic_expr : rel_expr ('&&' rel_expr)*
rel_expr : add_expr ('>' add_expr)*
add_expr : mul_expr ('+' mul_expr)*
mul_expr : unary ('*' unary)*
unary : factor | '-' unary
factor : id | num | ....

方法2： pratt解析

   1     +    2
     30    40

   1     *    2
     50     60

   1  +   2   *  3
        40  50

   1  +   2  +   3
       40   30
comment : '#' 非换行符号 '\r'? '\n'

cilly 词法
program : token* 'eof'

token
    : id | num | string
    | 'true' | 'false' | 'null'
    | 'var' | 'if' | 'else' | 'while' | 'continue' | 'break' | 'return' | 'fun'
    | '(' | ')' | '{' | '}' | ','
    | '=' | '=='
    | '+' | '-' | '*' | '/'
    | '!' | '!='
    | '>' | '>='
    | '<' | '<='
    | '&&' | '||'
    ;

num : [0-9]* + ('.' [0-9]*)?
string : '"' char* '"'
char : 不是双引号的字符
ws : (' ' | '\r' | '\n' | '\t)+

"""

def error(src, msg):
    raise Exception(f"{src} : {msg}")


def mk_tk(tag, val=None):
    return [tag, val]


def tk_tag(t):
    return t[0]


def tk_val(t):
    return t[1]


def make_str_reader(s, err):
    cur = None
    pos = -1

    def peek(p=0):
        if pos + p >= len(s):
            return "eof"
        else:
            return s[pos + p]

    def match(c):
        if c != peek():
            err(f"期望{c}, 实际{peek()}")

        return next()

    def next():
        nonlocal pos, cur

        old = cur
        pos = pos + 1
        if pos >= len(s):
            cur = "eof"
        else:
            cur = s[pos]

        return old

    next()
    return peek, match, next


cilly_op1 = ["(", ")", "{", "}","[", "]", ",", ";", "+", "-", "*", "/", "^", ":", "."]

cilly_op2 = {
    ">": ">=",
    "<": "<=",
    "=": "==",
    "!": "!=",
    "&": "&&",
    "|": "||",
}

cilly_keywords = [
    "var",
    "print",
    "if",
    "else",
    "while",
    "break",
    "continue",
    "return",
    "fun",
    "true",
    "false",
    "null",
    "for",
]


# 词法解析器
def cilly_lexer(prog):

    def err(msg):
        error("cilly lexer", msg)

    peek, match, next = make_str_reader(prog, err)

    def program():
        r = []

        while True:
            skip_ws()
            if peek() == "eof":
                break

            r.append(token())

        return r

    def skip_ws():
        while peek() in [" ", "\t", "\r", "\n"]:
            next()

    def token():

        c = peek()

        if is_digit(c):
            return num()

        if c in ["?", ":"]:
            next()
            return mk_tk(c)

        if c == '"':
            return string()

        if c == "_" or is_alpha(c):
            return id()

        if c in cilly_op1:
            next()
            return mk_tk(c)

        if c in cilly_op2:
            next()
            if peek() == cilly_op2[c][1]:
                next()
                return mk_tk(cilly_op2[c])
            else:
                return mk_tk(c)

        err(f"非法字符{c}")

    def is_digit(c):
        return c >= "0" and c <= "9"

    def num():
        r = ""

        while is_digit(peek()):
            r = r + next()

        if peek() == ".":
            r = r + next()

            while is_digit(peek()):
                r = r + next()

        return mk_tk("num", float(r) if "." in r else int(r))

    def string():
        match('"')

        r = ""
        while peek() != '"' and peek() != "eof":
            r = r + next()

        match('"')

        return mk_tk("str", r)

    def is_alpha(c):
        return (c >= "a" and c <= "z") or (c >= "A" and c <= "Z")

    def is_digit_alpha__(c):
        return c == "_" or is_digit(c) or is_alpha(c)

    def id():
        r = "" + next()

        while is_digit_alpha__(peek()):
            if peek() == "eof":
                break
            r = r + next()

        if r in cilly_keywords:
            return mk_tk(r)

        return mk_tk("id", r)

    return program()


EOF = mk_tk("eof")


def make_token_reader(ts, err):
    pos = -1
    cur = None
    opos = -1

    # 返回token标识符
    def peek(p=0):
        if pos + p >= len(ts):
            return "eof"
        else:
            return tk_tag(ts[pos + p])

    # 匹配给定字符，不是则报错，是则返回当前token
    def match(t):
        if peek() != t:
            err(f"期望{t},实际为{cur}")

        return next()

    # 读下一个token，返回当前token
    def next():
        nonlocal pos, cur

        old = cur
        pos = pos + 1

        if pos >= len(ts):
            cur = EOF
        else:
            cur = ts[pos]

        return old
    
    def mark():
        nonlocal opos
        opos = pos

    def backroll():
        nonlocal pos, cur
        pos = opos
        cur = ts[pos]

    next()

    return peek, match, next, mark, backroll


# 语法分析器
def cilly_parser(tokens):
    def err(msg):
        error("cilly parser", msg)

    def check(msg):
        if peek() == "eof":
            err(f"需要" + msg)

    peek, match, next, mark, backroll = make_token_reader(tokens, err)

    def program():

        r = []

        while peek() != "eof":
            r.append(statement())

        return ["program", r]

    def statement():
        t = peek()

        # 变量声明符
        if t == "var":
            return define_stat()

        if t == "print":
            return print_stat()

        if t == "if":
            return if_stat()

        if t == "while":
            return while_stat()

        if t == "break":
            return break_stat()

        if t == "continue":
            return continue_stat()

        if t == "return":
            return return_stat()

        if t == "{":
            return block_stat()

        if t == "for":  # 新增 'for'
            return for_stat()

        if t == "fun":  # 新增 'fun'
            return fun_stat()
    
    
        return assign_stat()

    def define_stat():
        match("var")

        id = tk_val(match("id"))

        match("=")

        e = expr()

        match(";")

        return ["define", id, e]

    def assign_stat():

        mark()

        id = expr()

        if peek() != "=":
            backroll()
            return expr_stat()

        match("=")

        e = expr()

        if peek() != ")":
            match(";")

        return ["assign", id, e]

    def print_stat():
        match("print")
        match("(")

        if peek() == ")":
            alist = []
        else:
            alist = args()

        match(")")
        match(";")

        return ["print", alist]

    def args():

        r = [expr()]

        while peek() == ",":
            match(",")
            r.append(expr())

        return r

    def if_stat():  # if ( expr ) statement (else statment)?
        match("if")
        match("(")
        cond = expr()
        match(")")

        check("一个语句")
        true_stat = statement()

        if peek() == "else":
            match("else")
            check("一个语句")
            false_stat = statement()
        else:
            false_stat = None
        return ["if", cond, true_stat, false_stat]

    def for_stat():
        match("for")
        match("(")

        init = assign_stat()
        # print(init)
        # match(";")
        cond = expr()
        # print(cond)
        match(";")
        step = assign_stat()
        # print(step)
        match(")")

        check("一个语句")
        body = statement()

        return ["for", init, cond, step, body]

    def fun_stat():
        match("fun")
        id = tk_val(match("id"))
        match("(")
        if peek() == ")":
            alist = []
        else:
            alist = params()
        match(")")
        check("一个语句")
        body = statement()
        return ["fun_def", id, alist, body]

    def while_stat():
        match("while")
        match("(")
        cond = expr()
        match(")")
        check("一个语句")
        body = statement()
        return ["while", cond, body]

    def continue_stat():
        match("continue")
        match(";")
        return ["continue"]

    def break_stat():
        match("break")
        match(";")
        return ["break"]

    def return_stat():
        match("return")
        if peek() != ";":
            e = expr()
        else:
            e = None
        match(";")
        return ["return", e]

    def block_stat():
        match("{")
        r = []
        check("一个语句")
        while peek() != "}":
            r.append(statement())

        match("}")
        return ["block", r]

    def expr_stat():
        e = expr()
        match(";")
        return ["expr_stat", e]

    def literal(bp=0):
        return next()

    def unary(bp):
        op = tk_tag(next())
        e = expr(bp)

        return ["unary", op, e]

    def fun_expr(bp=0):
        match("fun")
        match("(")
        if peek() == ")":
            plist = []
        else:
            plist = params()

        match(")")

        check("block_statement")
        body = block_stat()

        return ["fun_expr", plist, body]

    def params():
        r = [tk_val(match("id"))]

        while peek() == ",":
            match(",")
            r.append(tk_val(match("id")))

        return r

    def parens(bp=0):
        match("(")

        e = expr()

        match(")")

        return e

    def array_expr(bp=0):
        match("[")
        elements = []
        while True:
            if peek() == ",":
                elements.append(mk_tk("null"))
                match(",")
            elif peek() == "]":
                elements.append(mk_tk("null"))
                break    
            else:
                elements.append(expr()) 
                if peek() == "]":
                    break
                match(",")
        match("]")
        return ["array", elements]

    def struct_expr(bp=0):
        match("{")
        fields = {}
        if peek() != "}":
            key = tk_val(match("id"))
            match(":")
            value = expr()
            fields[key] = value
            while peek() == ",":
                match(",")
                key = tk_val(match("id"))
                match(":")
                value = expr()
                fields[key] = value                
        match("}")
        return ["struct", fields]

    op1 = {
        "id": (100, literal),
        "num": (100, literal),
        "str": (100, literal),
        "true": (100, literal),
        "false": (100, literal),
        "null": (100, literal),
        "-": (85, unary),
        "!": (85, unary),
        "fun": (98, fun_expr),
        "(": (100, parens),
        "[": (100, array_expr),
        "{" : (100, struct_expr),
    }

    def get_op1_parser(t):
        if t not in op1:
            err(f"非法token: {t}")

        return op1[t]

    def binary(left, bp):
        op = tk_tag(next())
        right = expr(bp)
        return ["binary", op, left, right]

    def if_expr(left, bp=0):
        match("?")
        true_expr = expr(bp)
        match(":")
        false_expr = expr(bp)
        return ["if_expr", left, true_expr, false_expr]

    def call(fun_expr, bp=0):
        match("(")
        if peek() != ")":
            alist = args()
        else:
            alist = []
        match(")")
        return ["call", fun_expr, alist]

    # def assign_expr(left, bp):
    #     # 处理形如 id = expr 的赋值表达式, 用于for循环
    #     if left[0] != "id":
    #         error(f"赋值表达式左侧必须为标识符，实际得到 {left}")

    #     match("=")
    #     value = expr(bp)
    #     return ["assign", left, value]

    def array_access_expr(left, bp=0):
        match("[")
        index = expr()
        match("]")
        return ["array_access", left, index]

    def struct_access_expr(left, bp=0):
        match(".")
        field = tk_val(match("id"))
        return ["struct_access", left, field]

    op2 = {
        "*": (80, 81, binary),
        "/": (80, 81, binary),
        "+": (70, 71, binary),
        "-": (70, 71, binary),
        # "=": (20, 21, assign_expr),
        "^": (90, 89, binary),  # 右结合
        ">": (60, 61, binary),
        ">=": (60, 61, binary),
        "<": (60, 61, binary),
        "<=": (60, 61, binary),
        "==": (50, 51, binary),
        "!=": (50, 51, binary),
        "&&": (40, 41, binary),
        "||": (30, 31, binary),
        "?": (20, 19, if_expr),  # 新增 '?'
        ":": (20, 21, None),  # 新增 ':'
        "(": (90, 91, call),
        "[": (90, 91, array_access_expr),
        ".": (90, 91, struct_access_expr),
    }

    def get_op2_parser(t):
        if t not in op2:
            return (0, 0, None)
        else:
            return op2[t]

    def expr(bp=0):

        check(f"一个表达式")

        r_bp, parser = get_op1_parser(peek())
        # print(f"peek() = {peek()}")
        left = parser(r_bp)
        # print(f"left = {left}")

        while True:
            l_bp, r_bp, parser = get_op2_parser(peek())
            if parser == None or l_bp <= bp:
                break

            left = parser(left, r_bp)

        return left

    return program()


def mk_num(i):
    return ["num", i]


def mk_str(s):
    return ["str", s]


TRUE = ["bool", True]
FALSE = ["bool", False]


def mk_bool(b):
    return TRUE if b else FALSE


def mk_proc(params, body):
    return ["proc", params, body]


NULL = ["null", None]


def val(v):
    return v[1]


def lookup_var(env, var):
    if var not in env:
        error("lookup var", f"未定义变量{var}")

    return env[var]


def set_var(env, var, val):
    if var not in env:
        error("set var", f"未定义变量{var}")

    env[var] = val


def define_var(env, var, val):
    if var in env:
        error("define var", f"变量已定义{var}")

    env[var] = val


def cilly_eval(ast, env):
    def err(msg):
        return error("cilly eval", msg)

    def ev_program(node, env):
        _, statements = node

        r = NULL

        for s in statements:
            r = visit(s, env)

        return r

    def ev_expr_stat(node, env):
        _, e = node
        return visit(e, env)

    def ev_print(node, env):
        _, args = node

        for a in args:
            print(val(visit(a, env)), end=" ")

        print("")

        return NULL

    def ev_for(node, env):
        _, init, cond, step, body = node
        visit(init, env)
        while True:
            cond_val = visit(cond, env)
            if not val(cond_val):
                break
            res = visit(body, env)
            if res and res[0] == "break":
                break
            visit(step, env)
        return NULL

    def ev_literal(node, env):
        tag, v = node

        if tag in ["num", "str"]:
            return node

        if tag in ["true", "false"]:
            return TRUE if tag == "true" else FALSE

        if tag == "null":
            return NULL

        err(f"非法字面量{node}")

    def ev_unary(node, env):
        _, op, e = node

        v = val(visit(e, env))

        if op == "-":
            return mk_num(-v)

        if op == "!":
            return FALSE if v else TRUE

        err(f"非法一元运算符{op}")

    def ev_binary(node, env):
        _, op, e1, e2 = node

        v1 = val(visit(e1, env))
        if op == "&&":
            if v1 == False:
                return FALSE
            else:
                return visit(e2, env)

        if op == "||":
            if v1 == True:
                return TRUE
            else:
                return visit(e2, env)

        v2 = val(visit(e2, env))

        if op == "+":
            return mk_num(v1 + v2)

        if op == "-":
            return mk_num(v1 - v2)

        if op == "*":
            return mk_num(v1 * v2)

        if op == "/":
            return mk_num(v1 / v2)

        if op == ">":
            return mk_bool(v1 > v2)
        if op == ">=":
            return mk_bool(v1 >= v2)
        if op == "<":
            return mk_bool(v1 < v2)
        if op == "<=":
            return mk_bool(v1 <= v2)
        if op == "==":
            return mk_bool(v1 == v2)
        if op == "!=":
            return mk_bool(v1 != v2)
        if op == "^":
            return mk_num(v1**v2)

        err(f"非法二元运算符{op}")

    def ev_if(node, env):
        _, cond, true_s, false_s = node

        if visit(cond, env) == TRUE:
            return visit(true_s, env)

        if false_s != None:
            return visit(false_s, env)

        return NULL

    def ev_if_expr(node, env):
        _, cond, true_e, false_e = node
        c = visit(cond, env)
        return visit(true_e, env) if val(c) else visit(false_e, env)

    def ev_while(node, env):
        _, cond, body = node

        r = NULL
        prev_r = NULL
        while visit(cond, env) == TRUE:
            r = visit(body, env)
            if r[0] == "break":
                r = prev_r
                break

            if r[0] == "continue":

                continue
            prev_r = r

        return r

    def ev_break(node, env):
        return ["break"]

    def ev_continue(node, env):
        return ["continue"]

    def ev_block(node, env):
        _, statements = node

        r = NULL

        for s in statements:
            r = visit(s, env)
            if r[0] in ["break", "continue"]:
                return r

        return r

    def ev_id(node, env):
        _, name = node

        return lookup_var(env, name)

    def ev_define(node, env):
        _, name, e = node
        v = visit(e, env)

        define_var(env, name, v)
        return NULL

    def ev_assign(node, env):
        _, target, value_expr = node
        value = visit(value_expr, env)
        # 根据左值类型处理
        if target[0] == "id":
            # 普通变量赋值
            set_var(env, target[1], value)
        elif target[0] == "array_access":
            # 数组元素赋值 arr[0] = 5
            arr_expr, index_expr = target[1], target[2]
            arr = visit(arr_expr, env)
            index = val(visit(index_expr, env))
            # 类型检查
            if arr[0] != "array":
                error("assign", "只能对数组类型进行索引赋值")
            if not isinstance(index, int):
                error("assign", "数组索引必须是整数")
            if index < 0 or index >= len(arr[1]):
                error("assign", f"数组索引越界: {index}")
            # 执行赋值
            arr[1][index] = value
        elif target[0] == "struct_access":
            # 结构体属性赋值 obj.field = 5
            obj_expr, field = target[1], target[2]
            obj = visit(obj_expr, env)
            # 类型检查
            if obj[0] != "struct":
                error("assign", "只能对结构体类型进行属性赋值")
            if field not in obj[1]:
                error("assign", f"不存在的字段: {field}")
            # 执行赋值
            obj[1][field] = value
        else:
            err("非法的左值表达式")
        return NULL

    def ev_return(node, env):
        _, e = node

        if e != None:
            return visit(e, env)
        else:
            return NULL

    def ev_fun_expr(node, env):
        _, params, body = node
        return mk_proc(params, body)

    def ev_fun_def(node, env):
        _, name, params, body = node
        define_var(env, name, ["proc", params, body])
        return NULL

    def ev_array(node, env):
        _, elements = node
        evaluated_elements = [visit(e, env) for e in elements]
        return ["array", evaluated_elements]

    def ev_struct(node, env):
        _, fields = node
        evaluated_fields = {}
        for key, value_expr in fields.items():
            evaluated_fields[key] = visit(value_expr, env)
        return ["struct", evaluated_fields]

    def ev_array_access(node, env):
        _, arr_expr, index_expr = node

        arr = visit(arr_expr, env)
        index = val(visit(index_expr, env))

        if arr[0] != "array":
            err("只能对数组类型进行索引访问")
        if not isinstance(index, int):
            err("数组索引必须是整数")
        if index < 0 or index >= len(arr[1]):
            err(f"数组索引越界: {index}")
        return arr[1][index]

    def ev_struct_access(node, env):
        _, obj_expr, field = node
        # 计算结构体实例
        obj = visit(obj_expr, env)

        # 类型检查
        if obj[0] != "struct":
            error("struct_access", "只能对结构体类型进行属性访问")
        if field not in obj[1]:
            error("struct_access", f"不存在的字段: {field}")
        return obj[1][field]

    def ev_call(node, env):
        _, f_expr, args = node
        f = visit(f_expr, env)
        if isinstance(f, list) and f[0] == "proc":
            _, params, body = f
            evaluated_args = [visit(a, env) for a in args]
            if len(params) != len(evaluated_args):
                err(f"参数数量不匹配: 期望 {len(params)} 个，实际 {len(evaluated_args)} 个")
            
            local_env = env.copy()
            for param, arg in zip(params, evaluated_args):
                local_env[param] = arg
            return visit(body, local_env)
        elif callable(f):
            evaluated_args = [val(visit(a, env)) for a in args]
            try:
                f(*evaluated_args)
                return NULL
            except Exception as e:
                err(f"调用 Python 函数时出错: {e}")
        else:
            err(f"非法函数: {f}")

    visitors = {
        "program": ev_program,
        "expr_stat": ev_expr_stat,
        "print": ev_print,
        "if": ev_if,
        "while": ev_while,
        "break": ev_break,
        "continue": ev_continue,
        "block": ev_block,
        "define": ev_define,
        "assign": ev_assign,
        "unary": ev_unary,
        "binary": ev_binary,
        "return": ev_return,
        "fun_expr": ev_fun_expr,
        "call": ev_call,
        "id": ev_id,
        "num": ev_literal,
        "str": ev_literal,
        "true": ev_literal,
        "false": ev_literal,
        "null": ev_literal,
        "for": ev_for,
        "fun_def": ev_fun_def,
        "if_expr": ev_if_expr,
        "array": ev_array,
        "struct": ev_struct,
        "array_access": ev_array_access,
        "struct_access": ev_struct_access,
    }

    def visit(node, env):
        tag = node[0]
        if tag not in visitors:
            err(f"非法节点{node}")

        return visitors[tag](node, env)

    return visit(ast, env)


# p1 = """

# var sum = 0;
# var i = 1;

# while(i <= 100){
#     sum = sum + i;
#     i = i + 1;
# }

# print("1+2+...100=",sum);

# var f0 = 0;
# var f1 = 1;

# var t = 0;

# i = 0;

# while(i < 10){
#     t = f1;
#     f1 = f0 + f1;
#     f0 = t;
#     i = i + 1;
# }

# print("fib(10)" , f0);

# var add = fun(a,b){
#     return a + b;
# };

# print(add(1,2), add(3*4, 6));

# print(2 ^ 3);

# fun sub(a, b){
#     return a - b;
# }

# print(sub(2,3));

# var ans = (1 + 1) ? 2 : 3;
# print(ans);

# i = 0;
# ans = 0;

# for(i = 1; i <= 10; i = i + 1){
#     ans = ans + i;
# }

# print(ans);

# """

# p1 = """
# var ans = 0;
# var i = 0;
# for(i = 1; i <= 10; i = i + 1)
# {
#     ans = ans + i;
# }
# print(ans);
# """
# p1 = """
# var a = fun(x, y){
#     return x + y;
# };
# fun b(x, y){
#     return x - y;
# }
# var x = b(1, 2);
# print(x);
# print(a(1, 2));
# """

# env = {}
# tokens = cilly_lexer(p1)
# print("tokens:")
# print(tokens)
# ast = cilly_parser(tokens)
# print("ast:")
# print(ast)
# v = cilly_eval(ast, env)
