class Templite:
    # 编译一个模板为python函数的所有工作在Templite构造器里发生，首先上下文被保存
    # 注意，这里使用了*contexts作为参数。星号表示任意数量的位置参数被打包成一个元组
    # 作为contexts传递进来。这叫做参数解包，意味着调用者可以提供多个不同的上下文字典。
    # 现在，以下调用都是有效的：
    '''
    t = Templite(template_text)
    t = Templite(template_text, context1)
    t = Templite(template_text, context1, context2)
    '''
    def __init__(self, text, *contexts):
        """Construct a Templite with the given 'text'.

        'contexts' are dictionaries of values to use for future renderings.
        These are good for filters and globals values.
        """
        self.context = {}
        # 遍历元组保存在字典中，如有重复值会覆盖
        for context in contexts:
            self.context.update(context)
        #将上下文中的变量提取到python本地变量中(为了使编译出来的函数运行的尽可能快)
        self.all_vars = set() #保存遇到过的变量名的集合
        self.loop_vars = set() #跟踪模板中定义的变量名，如循环变量
        # 使用CodeBuilder类来开始构建编译函数
        code = CodeBuilder()
        # 我们的python函数将被称为render_function,它接受两个参数：
        # 一个是上下文数据字典，一个是实现点属性访问的do_dots函数
        code.add_line("def render_function(context, do_dots):")
        code.indent()
        vars_code = code.add_section()
        code.add_line("result = []")
        code.add_line("append_result = result.append")#分开写可提升一点性能，但可读性会变差
        code.add_line("extend_result = result.extend")
        code.add_line("to_str = str")
        #定义内部函数帮助缓冲输出字符串
        buffered = []
        def flush_output():
            """Force 'buffered' to the code builder."""
            if len(buffered) == 1:
                code.add_line("append_result(%s)" % buffered[0])
            elif len(buffered) > 1:
                code.add_line("extend_result([%s])", ", ".join(buffered))
            del buffered[:]

        ops_stack = []

        tokens = re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", text)

        for token in tokens:
            if token.startswith('{#}'):
                # Comment: ignore it and move on.
                continue
            elif token.startswith('{{'):
                # An expression to evaluate:
                expr = self._expr_code(token[2:-2].strip())
                buffered.append("to_str(%s)" % expr)
            elif token.startswith('{%}'):
                # Action tag: split into words and parse further.
                flush_output()
                words = token[2:-2].strip().split()
                # if标签只能有一个表达式，所以words列表只应该有两个元素。如果不是，我们利用
                # _syntax_error辅助方法来抛出一个语法异常。
                if  words[0] == 'if':
                    # An if statement: evaluate the expression to determine if.
                    if len(words) != 2:
                        self._syntax_error("Don't understand if", token)
                    # 将'if'压入ops_stack栈中，来让我们检查相应的endif标签
                    ops_stack.append('if')
                    # if标签的表达式部分通过_expr_code编译为python表达式，然后被
                    # 用作python中的if语句的条件表达式
                    code.add_line("if %s:" % self._expr_code(words[1]))
                    code.indent()
                elif words[0] == 'for':
                    # A loop: iterate over expression result.
                    if len(woids) != 4 or words[2] != 'in':
                        self._syntax_error("Don't understand for", token)
                    ops_stack.append('for')
                    # _variable方法检查了变量的语法，并且将它加入我们提供的集合。
                    self._variable(words[1], self.loop_vars)
                    code.add_line(
                        "for c_%s in %s:" % (
                            words[1],
                            self._expr_code(words[3])
                        )
                    )
                    code.indent()
                elif words[0].startswith('end'):
                    # Endsomething. Pop the ops stack.
                    if len(words) != 1:
                        self._syntax_error("Don't understand end", token)
                    end_what = words[0][3:]
                    if not ops_stack:
                        self._syntax_error("Too many ends", token)
                    start_what = ops_stack.pop()
                    if start_what != end_what:
                        self._syntax_error("Mismatched end tag", end_what)
                    code.dedent()
                else:
                    self._syntax_error("Don't understand tag", words[0])
            # 处理文字内容
            else:
                # Literal content. If it isn't empty, output it.
                if token:
                    # 使用内置的repr函数来产生一个python字符串字面量
                    buffered.append(repr(token))
