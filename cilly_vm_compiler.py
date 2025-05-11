from cilly_interpreter import error
from cilly_interpreter import mk_num, mk_str, mk_bool, val, NULL, TRUE, FALSE

from cilly_interpreter import cilly_lexer, cilly_parser

"""
very simple stack machine
"""

# 3 + 5 * 6

# PUSH = 1
# ADD = 2
# SUB = 3
# MUL = 4
# DIV = 5

# POP = 6

# PRINT = 7

# p1 = [
#     PUSH,
#     3,
#     PUSH,
#     5,
#     PUSH,
#     6,
#     MUL,
#     ADD,
#     PRINT,
# ]

class Stack:
    def __init__(self):
        self.stack = []
        self.push_count = 0 #记录 push 次数
        self.pop_count = 0  #记录 pop 次数
        self.current_depth = 0 #记录当前栈的深度
        self.max_depth = 0   #记录栈的最大深度
        
    def push(self, v):
        self.stack.append(v)
        self.push_count += 1
        self.current_depth += 1
        if self.current_depth > self.max_depth:
            self.max_depth = self.current_depth
        
    def pop(self):
        if self.empty():
            raise RuntimeError("Stack underflow")
        self.pop_count += 1
        self.current_depth -= 1
        return self.stack.pop()
    
    def top(self):
        return self.stack[-1]
    
    def empty(self):
        return len(self.stack) == 0
   
  
# def simple_stack_vm(code):
    
#     pc = 0
    
#     def err(msg):
#         error('simple stack machine', msg)
        
#     stack = Stack()
    
#     def push(v):
#         return stack.push(v)
    
#     def pop():
#         return stack.pop()
    
    
#     while pc < len(code):
        
#         opcode = code[pc]
        
#         if opcode == PUSH:
#             v = code[pc+1]
#             push(v)
#             pc = pc + 2
#         elif opcode == PRINT:
#             v = pop()
#             print(v)
#             pc = pc + 1
#         elif opcode == ADD:
#             v2 = pop()
#             v1 = pop()
#             push(v1 + v2)
#             pc = pc + 1
#         elif opcode == SUB:
#             v2 = pop()
#             v1 = pop()
#             push(v1 - v2)
#             pc = pc + 1
#         elif opcode == MUL:
#             v2 = pop()
#             v1 = pop()
#             push(v1 * v2)
#             pc = pc + 1
#         elif opcode == DIV:
#             v2 = pop()
#             v1 = pop()
#             push(v1 / v2)
#             pc = pc + 1
#         else:
#             err(f'非法opcode: {opcode}')

'''
cilly vm: stack machine
'''

LOAD_CONST = 1

LOAD_NULL = 2
LOAD_TRUE = 3
LOAD_FALSE = 4

LOAD_VAR = 5        # 后需跟两个参数，第一个是作用域索引，第二个是变量索引
STORE_VAR = 6       # 后需跟两个参数，第一个是作用域索引，第二个是变量索引

PRINT_ITEM = 7
PRINT_NEWLINE = 8

JMP = 9
JMP_TRUE = 10
JMP_FALSE = 11

POP = 12

ENTER_SCOPE = 13    #后需跟一个参数，表示该作用域内变量数量
LEAVE_SCOPE = 14

MAKE_PROC = 15
CALL = 16
RETURN = 17

UNARY_NEG = 101
UNARY_NOT = 102

BINARY_ADD = 111
BINARY_SUB = 112
BINARY_MUL = 113
BINARY_DIV = 114
BINARY_MOD = 115
BINARY_POW = 116

BINARY_EQ = 117
BINARY_NE = 118
BINARY_LT = 119  # <
BINARY_GE = 120  # >=

OPS_NAME = {
    LOAD_CONST: ("LOAD_CONST", 2),
    LOAD_NULL: ("LOAD_NULL", 1),
    LOAD_TRUE: ("LOAD_TRUE", 1),
    LOAD_FALSE: ("LOAD_FALSE", 1),
    LOAD_VAR: ("LOAD_VAR", 3),
    STORE_VAR: ("STORE_VAR", 3),
    PRINT_ITEM: ("PRINT_ITEM", 1),
    PRINT_NEWLINE: ("PRINT_NEWLINE", 1),
    POP: ("POP", 1),
    ENTER_SCOPE: ("ENTER_SCOPE", 2),
    LEAVE_SCOPE: ("LEAVE_SCOPE", 1),
    MAKE_PROC: ("MAKE_PROC", 1),
    CALL: ("CALL", 2),
    RETURN: ("RETURN", 1),
    JMP: ("JMP", 2),
    JMP_TRUE: ("JMP_TRUE", 2),
    JMP_FALSE: ("JMP_FALSE", 2),
    UNARY_NEG: ("UNARY_NEG", 1),
    UNARY_NOT: ("UNARY_NOT", 1),
    BINARY_ADD: ("BINARY_ADD", 1),
    BINARY_SUB: ("BINARY_SUB", 1),
    BINARY_MUL: ("BINARY_MUL", 1),
    BINARY_DIV: ("BINARY_DIV", 1),
    BINARY_MOD: ("BINARY_MOD", 1),
    BINARY_POW: ("BINARY_POW", 1),
    BINARY_EQ: ("BINARY_EQ", 1),
    BINARY_NE: ("BINARY_NE", 1),
    BINARY_LT: ("BINARY_LT", 1),
    BINARY_GE: ("BINARY_GE", 1),
}


def cilly_vm(code, consts, scopes):

    def err(msg):
        error("cilly vm", msg)

    stack = Stack()
    call_stack = Stack()

    def push(v):
        stack.push(v)

    def pop():
        return stack.pop()

    # load 指令进行压栈操作用于运算或赋值
    def load_const(pc):

        index = code[pc + 1]
        v = consts[index]

        push(v)

        return pc + 2

    def load_null(pc):
        push(NULL)

        return pc + 1

    def load_true(pc):
        push(TRUE)
        return pc + 1

    def load_false(pc):
        push(FALSE)
        return pc + 1

    def load_var(pc):
        scope_i = code[pc + 1]  # 作用域索引
        if scope_i >= len(scopes):
            err(f"作用域索引超出访问: {scope_i}")

        scope = scopes[-scope_i - 1]

        index = code[pc + 2]  # 变量索引
        if index >= len(scope):
            err(f"load_var变量索引超出范围:{index}")

        push(scope[index]) # 压栈进行运算

        return pc + 3

    # 存储变量到作用域中
    def store_var(pc):
        scope_i = code[pc + 1]
        if scope_i >= len(scopes):
            err(f"作用域索引超出访问: {scope_i}")

        scope = scopes[-scope_i - 1]  # 定位目标作用域（从外向内数第 scope_i 个作用域）

        index = code[pc + 2]
        if index >= len(scope):
            err(f"load_var变量索引超出范围:{index}")

        scope[index] = pop()

        return pc + 3
    # 创建作用域用于存储该作用域下的变量
    def enter_scope(pc):
        var_count = code[pc + 1]

        scope = [NULL for _ in range(var_count)]
        nonlocal scopes

        scopes = scopes + [scope]  # 不用scopes.append(scope)

        return pc + 2

    def leave_scope(pc):
        nonlocal scopes
        scopes = scopes[:-1]  # 不用scopes.pop()

        return pc + 1

    def make_proc(pc):
        tag, proc_entry, param_count = pop()

        if tag != 'fun':
            err(f"非法函数定义: {tag}")

        push(("compiled_proc", proc_entry, param_count, scopes))    
        return pc + 1
    def call(pc):

        arg_count = code[pc + 1]
        return_addr = pc + 2

        nonlocal scopes
        call_stack.push((return_addr, scopes))

        scope = []
        for _ in range(arg_count):
            scope.append(pop())
        scope.reverse()

        tag, proc_entry, param_count, outer_scopes = pop()

        if tag != "compiled_proc":
            err(f"非法调用: {tag}")
        if param_count != arg_count:
            err(f"参数个数不匹配: {param_count} != {arg_count}")
 
        scopes = outer_scopes + [scope]

        return proc_entry

    def ret(pc):
        nonlocal scopes
        return_addr, scopes = call_stack.pop()
        return return_addr
    def print_item(pc):
        v = val(pop())
        print(v, end=" ")
        return pc + 1

    def print_newline(pc):
        print("")

        return pc + 1

    def pop_proc(pc):
        pop()
        return pc + 1

    def jmp(pc):
        target = code[pc + 1]

        return target

    def jmp_true(pc):
        target = code[pc + 1]

        if pop() == TRUE:
            return target
        else:
            return pc + 2

    def jmp_false(pc):
        target = code[pc + 1]

        if pop() == FALSE:
            return target
        else:
            return pc + 2

    def unary_op(pc):
        v = val(pop())

        opcode = code[pc]

        if opcode == UNARY_NEG:
            push(mk_num(-v))
        elif opcode == UNARY_NOT:
            push(mk_bool(not v))
        else:
            err(f"非法一元opcode: {opcode}")

        return pc + 1

    # 执行二元运算并压栈
    def binary_op(pc):
        v2 = val(pop())
        v1 = val(pop())

        opcode = code[pc]

        if opcode == BINARY_ADD:
            push(mk_num(v1 + v2))
        elif opcode == BINARY_SUB:
            push(mk_num(v1 - v2))
        elif opcode == BINARY_MUL:
            push(mk_num(v1 * v2))
        elif opcode == BINARY_DIV:
            push(mk_num(v1 / v2))
        elif opcode == BINARY_MOD:
            push(mk_num(v1 % v2))
        elif opcode == BINARY_POW:
            push(mk_num(v1**v2))
        elif opcode == BINARY_EQ:
            push(mk_bool(v1 == v2))
        elif opcode == BINARY_NE:
            push(mk_bool(v1 != v2))
        elif opcode == BINARY_LT:
            push(mk_bool(v1 < v2))
        elif opcode == BINARY_GE:
            push(mk_bool(v1 >= v2))
        else:
            err(f"非法二元opcode:{opcode}")

        return pc + 1

    ops = {
        LOAD_CONST: load_const,
        LOAD_NULL: load_null,
        LOAD_TRUE: load_true,
        LOAD_FALSE: load_false,
        LOAD_VAR: load_var,
        STORE_VAR: store_var,
        ENTER_SCOPE: enter_scope,
        LEAVE_SCOPE: leave_scope,
        MAKE_PROC: make_proc,
        CALL: call,
        RETURN: ret,
        PRINT_ITEM: print_item,
        PRINT_NEWLINE: print_newline,
        POP: pop_proc,
        JMP: jmp,
        JMP_TRUE: jmp_true,
        JMP_FALSE: jmp_false,
        UNARY_NEG: unary_op,
        UNARY_NOT: unary_op,
        BINARY_ADD: binary_op,
        BINARY_SUB: binary_op,
        BINARY_MUL: binary_op,
        BINARY_DIV: binary_op,
        BINARY_MOD: binary_op,
        BINARY_POW: binary_op,
        BINARY_EQ: binary_op,
        BINARY_NE: binary_op,
        BINARY_LT: binary_op,
        BINARY_GE: binary_op,      
    }
    
    def get_opcode_proc(opcode):
        if opcode not in ops:
            err(f'非法opcode: {opcode}')
            
        return ops[opcode]
    
    def run():
        pc = 0
        
        while pc < len(code):
            opcode = code[pc]
            
            proc = get_opcode_proc(opcode)
            
            pc = proc(pc)
                            
    run()
    # 输出栈统计信息
    print("\n--- Stack Statistics ---")
    print(f"Push count: {stack.push_count}")
    print(f"Pop count: {stack.pop_count}")
    print(f"Max stack depth: {stack.max_depth}")
    print(f"Final stack depth: {stack.current_depth}")
           
consts = [
    mk_num(3),
    mk_num(5),
    mk_num(6),
]
vars = [
    mk_num(100),  # a
    mk_num(200),  # b,
    NULL,  # c
]
# 3 + 5 * 6

p1 = [
    LOAD_CONST, 0,
    LOAD_CONST, 1,
    LOAD_CONST, 2,
    BINARY_MUL,
    BINARY_ADD,
    PRINT_ITEM,
    PRINT_NEWLINE,
]

# cilly_vm(p1, consts, vars)
# c = a + b * 5

p1 = [
    LOAD_VAR,
    0,  # push a
    LOAD_VAR,
    1,  # push b
    LOAD_CONST,
    1,  # push 5
    BINARY_MUL,  # b * 5
    BINARY_ADD,  # a + b * 5
    STORE_VAR,
    2,  # c = pop()
    LOAD_VAR,
    2,  # push c
    PRINT_ITEM,  # print c
    PRINT_NEWLINE,
]

# cilly_vm(p1, consts, vars)
"""
var i = 1;
var sum = 0;

while (i <= 100){
    sum = sum + i;
    i = i + 1;
}

print(sum);
"""

consts = [
    mk_num(0),
    mk_num(1),
    mk_num(100),
]
vars = [
    NULL,  # i
    NULL,  # sum
]

p1 = [
    # i = 1
    LOAD_CONST, 1,
    STORE_VAR, 0,
    
    # sum = 0
    LOAD_CONST, 0,
    STORE_VAR, 1,
    
    # while ( i <= 100 ) {
    LOAD_CONST, 2,
    LOAD_VAR, 0,
    BINARY_LT,
    
    JMP_TRUE, 31, #i > 100退出while循环
    
    #sum = sum + i
    LOAD_VAR, 1,
    LOAD_VAR, 0,
    BINARY_ADD,
    STORE_VAR, 1,
    
    #i = i + 1
    LOAD_VAR, 0,
    LOAD_CONST, 1,
    BINARY_ADD,
    STORE_VAR, 0,
    
    JMP, 8,
    #}
    
    # print sum
    LOAD_VAR, 1,
    PRINT_ITEM,
    PRINT_NEWLINE,
    
]
#cilly_vm(p1, consts, vars)

def sum100():
    i = 1
    sum = 0
    while i <= 100:
        sum = sum + i
        i = i + 1        
    print(sum)
        
'''
cilly vm反汇编器
'''

def cilly_vm_dis(code, consts, var_names):
    
    def err(msg):
        error('cilly vm disassembler', msg)
        
    pc = 0
    
    while pc < len(code):
        opcode = code[pc]
        
        if opcode == LOAD_CONST:
            index = code[pc + 1]
            v = consts[index]
            
            print(f'{pc}\t LOAD_CONST {index} ({v})')
            
            pc = pc + 2
        elif opcode == LOAD_VAR:
            scope_i = code[pc + 1]
            index = code[pc + 2]
            v = var_names[(scope_i, index, 'L')]

            print(f'{pc}\t LOAD_VAR {scope_i} {index} ({v})')
            pc = pc + 3
        
        elif opcode == STORE_VAR:
            scope_i = code[pc + 1]
            index = code[pc + 2]
            v = var_names[(scope_i, index, 'S')]

            print(f'{pc}\t STORE_VAR {scope_i} {index} ({v})')
            pc = pc + 3

        elif opcode in OPS_NAME:
            name, size = OPS_NAME[opcode]
            
            print(f'{pc}\t {name}', end='')
            
            if size > 1:
                print(f' {code[pc+1]}', end='')
                if size > 2:
                    print(f' {code[pc+2]}', end='')
                    
            print('')
            pc = pc + size
        else:
            err(f'非法opcode:{opcode}')
        
# vars_name = [
#     'i',
#     'sum',
# ]

vars_name = {}

#cilly_vm_dis(p1, consts, vars_name)

'''
Cilly vm compiler
'''

def cilly_vm_compiler(ast, code, consts, scopes):
    
    def err(msg):
        error('cilly vm compiler', msg)
    
    def add_const(c):
        for i in range(len(consts)):
            if consts[i] == c:
                return i

        consts.append(c)
        return len(consts) - 1

    def get_next_emit_addr():
        return len(code)

    def emit(opcode, operand1=None, operand2=None):

        addr = get_next_emit_addr()  # 获取当前code长度作为地址

        code.append(opcode)

        if operand1 != None:
            code.append(operand1)

        if operand2 != None:
            code.append(operand2)

        return addr

    def backpatch(addr, operand1=None, operand2=None):
        if operand1 != None:
            code[addr + 1] = operand1

        if operand2 != None:
            code[addr + 2] = operand2

    # 在作用域内部添加变量名，返回末尾索引
    def define_var(name):
        scope = scopes[-1]

        for i in range(len(scope)):
            if scope[i] == name:
                err(f"已定义变量: {name}")

        scope.append(name)
        return len(scope) - 1

    # Cilly 语言支持块级作用域（通过 block 实现），因此变量可能定义在多个嵌套的作用域中。lookup_var 能够从最内层作用域向外查找，确保访问到最近定义的变量。
    def lookup_var(name):
        for scope_i in range(len(scopes)):
            scope = scopes[-scope_i - 1]

            for index in range(len(scope)):
                if scope[index] == name:
                    return scope_i, index

        err(f"未定义变量：{name}")

    def compile_program(node):
        _, statements = node

        visit(["block", statements])

        # for s in statements:
        #    visit(s)

    def compile_expr_stat(node):
        _, e = node

        visit(e)

        emit(POP)

    def compile_print(node):
        _, args = node

        for a in args:
            visit(a)
            emit(PRINT_ITEM)

        emit(PRINT_NEWLINE)

    # 一定会进行压栈操作
    def compile_literal(node):
        tag = node[0]

        if tag == "null":
            emit(LOAD_NULL)
        elif tag == "true":
            emit(LOAD_TRUE)
        elif tag == "false":
            emit(LOAD_FALSE)
        elif tag in ["num", "str"]:
            index = add_const(node)  # 返回常量在consts中的索引
            emit(LOAD_CONST, index)  # LOAD_CONST INDEX

    def compile_unary(node):
        _, op, e = node

        visit(e)
        if op == "-":
            emit(UNARY_NEG)
        elif op == "!":
            emit(UNARY_NOT)
        else:
            err(f"非法一元运算符：{op}")

    def compile_binary(node):
        _, op, e1, e2 = node

        if op == "&&":
            visit(e1)

            # 如果第一个条件为 false 则直接跳转不需要判断接下来的条件，直接跳转到LOAD_FALSE
            addr1 = emit(JMP_FALSE, -1)

            visit(e2)
            # 如果在第一个条件为true情况下，直接跳过LOAD_FALSE指令，因为它是为第一个条件判断设置的
            # 栈里存的结果就是整个条件语句的结果
            addr2 = emit(JMP, -1)
            backpatch(addr1, get_next_emit_addr())
            # 将整个条件语句设置为 false
            emit(LOAD_FALSE)
            backpatch(addr2, get_next_emit_addr())
            return

        if op == "||":
            visit(e1)

            addr1 = emit(JMP_TRUE, -1)

            visit(e2)
            addr2 = emit(JMP, -1)
            backpatch(addr1, get_next_emit_addr())
            emit(LOAD_TRUE)
            backpatch(addr2, get_next_emit_addr())

            return

        if op in [">", "<="]:
            visit(e2)
            visit(e1)
            if op == ">":
                emit(BINARY_LT)
            else:
                emit(BINARY_GE)

            return

        visit(e1)
        visit(e2)

        if op == "+":
            emit(BINARY_ADD)
        elif op == "-":
            emit(BINARY_SUB)
        elif op == "*":
            emit(BINARY_MUL)
        elif op == "/":
            emit(BINARY_DIV)
        elif op == "%":
            emit(BINARY_MOD)
        elif op == "^":
            emit(BINARY_POW)
        elif op == "==":
            emit(BINARY_EQ)
        elif op == "!=":
            emit(BINARY_NE)
        elif op == "<":
            emit(BINARY_LT)
        elif op == ">=":
            emit(BINARY_GE)
        else:
            err(f"非法二元运算符：{op}")

    def compile_if(node):
        _, cond, true_s, false_s = node

        visit(cond)
        addr1 = emit(JMP_FALSE, -1)

        visit(true_s)
        if false_s == None:
            backpatch(addr1, get_next_emit_addr())
        else:
            addr2 = emit(JMP, -1)

            backpatch(addr1, get_next_emit_addr())

            visit(false_s)
            backpatch(addr2, get_next_emit_addr())

    def compile_block(node):
        _, statements = node

        nonlocal scopes
        scope = []

        # compiler scope: name
        scopes = scopes + [scope]

        # vm scope: value
        addr = emit(ENTER_SCOPE, -1)

        for s in statements:
            tag = s[0]
            if tag == "define":
                _, name, e = s
                define_var(name)

        for s in statements:
            visit(s)

        emit(LEAVE_SCOPE)
        backpatch(addr, len(scope))

        scopes = scopes[:-1]

    def compile_define(node):
        _, name, e = node

        # index = define_var(name)
        _, index = lookup_var(name)
        visit(e)

        emit(STORE_VAR, 0, index)
        vars_name[(0, index, 'S')] = name

    def compile_assign(node):
        _, name, e = node

        # 把赋值的表达式的值压入栈中
        visit(e)

        scope_i, index = lookup_var(val(name))
        emit(STORE_VAR, scope_i, index)
        vars_name[(scope_i, index, 'S')] = val(name)

    def compile_id(node):
        _, name = node

        scope_i, index = lookup_var(name)
        emit(LOAD_VAR, scope_i, index)
        vars_name[(scope_i, index, 'L')] = name

    def compile_fun(node):
        _, params, body = node

        params_count = len(params)
        scope = [p for p in params]

        nonlocal scopes
        scopes = scopes + [scope]

        addr1 = emit(LOAD_CONST, -1)
        emit(MAKE_PROC)
        addr2 = emit(JMP, -1)

        proc_entry = get_next_emit_addr()

        visit(body)

        emit(LOAD_NULL)
        emit(RETURN)

        backpatch(addr2, get_next_emit_addr())
        index = add_const(("fun", proc_entry, params_count))
        backpatch(addr1, index)

        scopes = scopes[:-1]
    def compile_return(node):
        _, e = node

        if e == None:
            emit(LOAD_NULL)
        else:
            visit(e)

        emit(RETURN)    
    def compile_call(node):
        _, fun_expr, args = node

        visit(fun_expr)

        for a in args:
            visit(a)

        emit(CALL, len(args))
    
    while_stack = Stack()
    def compile_while(node):
        _, cond, body = node
        loop_start = get_next_emit_addr()
        while_stack.push((loop_start, [], get_current_scopes_depth()))
        visit(cond)
        false_addr = emit(JMP_FALSE, -1) #判断循环条件，当条件为false时跳转到循环结束位置，当前位置未知，暂定-1，以后回填
        visit(body)
        emit(JMP, loop_start) #循环代码执行完毕，跳转到循环开始，再进行条件判定
        loop_over = get_next_emit_addr() #整个循环体逻辑执行完毕，记录循环结束的opcode位置
        _, breaklist, _ = while_stack.pop()
        for b in breaklist:             #回填代码中出现的所有break
            backpatch(b, loop_over)   
        backpatch(false_addr, loop_over) #回填false条件的addr
    
   def compile_break(node):   #如果出现break语句，跳转到当前循环结束，但是结束位置未知
        _, breaklist, saved_depth = while_stack.top()
        for i in range(0, get_current_scopes_depth() - saved_depth):
            emit(LEAVE_SCOPE)    #注意要在跳转之前退出作用域，否则本指令将被JMP忽略掉
        break_addr = emit(JMP, -1)
        breaklist.append(break_addr) #在当前循环暂存break_addr，当循环其它代码转换为opcode后回填
        
    
   def compile_continue(node): #如果出现continue语句，直接跳转到当前循环开始
        loop_start, _ , saved_depth = while_stack.top()
        for i in range(0, get_current_scopes_depth() - saved_depth):
            emit(LEAVE_SCOPE)
        emit(JMP, loop_start)

    visitors = {
        "program": compile_program,
        "expr_stat": compile_expr_stat,
        "print": compile_print,
        "if": compile_if,
        'while': compile_while,
        'break': compile_break,
        'continue': compile_continue,
        #
        "define": compile_define,
        "assign": compile_assign,
        #
        "block": compile_block,
        #
        "unary": compile_unary,
        "binary": compile_binary,
        #
        "id": compile_id,
        #
        'fun_expr': compile_fun,
        'fun_def': compile_fun,
        'return': compile_return,
        'call': compile_call,
        #
        "num": compile_literal,
        "str": compile_literal,
        "true": compile_literal,
        "false": compile_literal,
        "null": compile_literal,
    }

    def visit(node):
        tag = node[0]

        if tag not in visitors:
            err(f"非法ast节点: {tag}")

        v = visitors[tag]

        v(node)

    visit(ast)
    return code, consts, scopes


p1 = """
var i = 2;
"""

# p1 = """
# 1 + 2 * 3;
# print(3 *4 - 5, 6 / 2);
# """

# p1 = """
# print(false && true);
# """

# p1 = """
# if(1 > 2)
#     print(3);
# else
#     print(4);
# """

# p1 = """
# if( 1 > 2)
#     print(3);
# print(4);
# """

# p1 = """
# if( 1 > 2 && 5 > 4)
#     print(30);
# else
#     print(42);
# """

# p1 = '''
# var i = 0;
# while(i < 5)
# {
#     print(i);
#     i = i + 1;
# }

# p1 = '''
# var i = 0;
# while(i < 5)
# {
#    if (i == 3)
#    {
#       print("执行break，终端循环");
#       break;
#    }
#    print(i);
#    i = i + 1;
# }

# p1 = '''
# var i = 5;
# var x = 3;
# while(i > 0)
# {
#    while(x > 0)
#    {
#       if (x == 2)
#       {
#          print("此时x = 2, 执行break，退出循环");
#          break;
#       }
#       print(x);
#       x = x - 1;
#    }
#    i = i - 1;
#    if (i == 4)
#    {
#       print("执行continue,不输出4");
#       continue;
#    }
#    print(i);
# }

p1 = """
var add = fun(a, b){
  return a + b;
};
var odd = fun(n){
  if(n == 0)
    return false;
  else
   return even(n-1);
};
var even = fun(n) {
 if(n==0)
   return true;
 else
   return odd(n-1);
};
{
    print(even(3), odd(3));
    var x = fun(a, b){
        return a + b;
    };
    var y = fun(a, b){
        return a * b;
    };
    print(x(1, 2), y(1, 2));
}
print(add(1,2));
print(even(3), odd(3));
"""

ts = cilly_lexer(p1)
ast = cilly_parser(ts)
print(ast)
code, consts, scopes = cilly_vm_compiler(ast, [], [], [])
print(code)
print(consts)
cilly_vm_dis(code, consts, ["i"])
cilly_vm(code, consts, scopes)
        

