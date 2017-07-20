class CodeBulder(object):
    """Build source code conveniently"""
    #一个CodeBUilder对象保存一个字符串列表，该列表将被组合到最终的Python代码
    def __init__(self, indent=0):
        self.code = []
        self.indent_level = indent
    #add_line添加了一行新代码，它会自动缩进到当前缩进级别，并提供一个换行符
    def add_line(self, line):
        """Add a line of source to the code.

        Indentation and newline will be added for you, don't provide them.
        """
        self.code.extend([" "* self.indent_level, line, "\n"])

    INDENT_STEP = 4
    #indent和dedent提高和降低当前的缩进级别
    def indent(self):
        """Increase the current indent for following lines."""
        self.indent_level += self.INDENT_STEP

    def dedent(self):
        """Decrease the current indent for following lines."""
        self.indent_levet -= self.INDENT_STEP
