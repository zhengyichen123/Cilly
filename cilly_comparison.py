import time
from cilly_interpreter import cilly_parser, cilly_lexer, cilly_eval
from cilly_vm_compiler import cilly_vm_compiler, cilly_vm


def time_interpreter(test_code, runs=100):
    total = 0
    for _ in range(runs):
        env = {}
        tokens = cilly_lexer(test_code)
        ast = cilly_parser(tokens)


        start = time.perf_counter()
        cilly_eval(ast, env)
        total += time.perf_counter() - start

    avg_time = total / runs
    print(f"[解释器] 平均耗时 ({runs}次): {avg_time:.6f}秒")
    return avg_time


def time_vm_compiler(test_code, runs=100):
    total = 0
    tokens = cilly_lexer(test_code)
    ast = cilly_parser(tokens)

    code, consts, scopes = cilly_vm_compiler(ast, [], [], [])

    for _ in range(runs):
        start = time.perf_counter()
        cilly_vm(code.copy(), consts.copy(), [])
        total += time.perf_counter() - start

    avg_time = total / runs
    print(f"[虚拟机] 平均耗时 ({runs}次): {avg_time:.6f}秒")
    return avg_time


if __name__ == "__main__":
    test_code = """
    var i = 5;
    var x = 3;
    while(i > 0)
    {
       while(x > 0)
       {
          if (x == 2)
          {
             print("此时x = 2, 执行break，退出循环");
             break;
          }
          print(x);
          x = x - 1;
       }
       i = i - 1;
       if (i == 4)
       {
          print("执行continue,不输出4");
          continue;
       }
       print(i);
    }
    """

    runs = 1000
    interpreter_avg = time_interpreter(test_code, runs)
    vm_avg = time_vm_compiler(test_code, runs)

    print(f"速度提升: {interpreter_avg / vm_avg:.1f}倍")