DIGITS = "0123456789"

# Token type => TT
TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_PLUS = "PLUS"  # 加
TT_MINUS = "MINUS"  # 减
TT_MUL = "MUL"  # 乘
TT_DIV = "DIV"  # 除
TT_LPAREN = "LPAREN"  # 左括号
TT_RPAREN = "RPAREN"  # 右括号
TT_EOF = "EOF"  # 终止符

"""
自定义 Error
"""


class Error(object):
    def __init__(self, pos_start, pos_end, error_name, details):
        """
        :param pos_start: 错误起始位置
        :param pos_end: 错误结束位置
        :param error_name: 错误名字
        :param details: 错误细节
        """

        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        res = f'{self.error_name}: {self.details}'
        res += f'File {self.pos_start.fn}, line {self.pos_end.ln + 1}'
        return res


"""
非法字符
"""


class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, detail):
        super().__init__(pos_start, pos_end, "Illegal Character", detail)


"""
无效语法
"""


class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, detail=''):
        super().__init__(pos_start, pos_end, "Invalid Syntax", detail)


"""
词法单元
"""


class Token(object):
    # type - value
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:  # Token 单个字符 + -> pos_start == pos_end
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance(self.value)  # 传入 current_char 读取下一个 Token

        if pos_end:  # Token 多个字符 123456
            self.pos_end = pos_end

    # 方便调试时，信息的查看
    def __repr__(self):
        if self.value:
            return f'{self.type}: {self.value}'
        return f'{self.type}'


class Position(object):
    def __init__(self, idx, ln, col, fn, ftxt):
        """
        :param idx: 索引
        :param ln: 行号
        :param col: 列号
        :param fn: 文件来源
        :param ftxt: 文件内容
        """
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    # 预读
    def advance(self, current_char):
        """
        :param current_char: 当前字符
        :return:
        """
        self.idx += 1  # 索引 + 1
        self.col += 1  # 列号 + 1

        if current_char == '\n':
            self.col = 0  # 列号归 0
            self.ln += 1  # 行号 + 1

    # 实例化Position
    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


"""
词法解析器
"""


class Lexer(object):
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None  # 当前的字符
        self.advance()

    # 预读
    def advance(self):
        self.pos.advance(self.current_char)  # 此时已经 self.pos.idx + 1
        if self.pos.idx < len(self.text):
            self.current_char = self.text[self.pos.idx]  # text => string, 可以根据索引取下一个位置
        else:
            self.current_char = None

    # 通过 advance() 遍历 text，并判断遍历的结果是否为关键字
    def make_tokens(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in (' ', '\t'):  # 若为空格或者制表符，词法分析器则自动跳过，不作处理
                self.advance()  # 往下读取
            elif self.current_char in DIGITS:  # 数字
                tokens.append(self.make_number())  # 通过调用 make_number() 将该数字添加到词法单元里面
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            else:  # 没有匹配到，非法字符错误
                # python 引用性调用 错误提示中包含当前位置，所以需要把当前位置 copy 出来
                # 若不 copy，则在操作该数据时，原本数据也会遭受影响
                pos_start = self.pos.copy()
                char = self.current_char  # 报错的那个字节
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")
        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    # 整数、小数 => 0.1  （0 小数点 1）
    def make_number(self):
        num_str = ''  # 最终识别出来的结果
        dot_count = 0  # 小数点的个数

        while self.current_char is not None and self.current_char in DIGITS + '.':  # DIGITS + '.' => "0123456789."
            if self.current_char == '.':
                if dot_count == 1:
                    break
                dot_count += 1
                num_str += '.'
            else:  # 当前字符不为小数点时，添加到 num_str 中
                num_str += self.current_char
            self.advance()  # 往下读，获取下一个
        if dot_count == 0:  # 若为整数
            return Token(TT_INT, int(num_str))  # 强制转换成 int
        else:
            return Token(TT_FLOAT, float(num_str))  # 强制转换成 float


"""
数字结点
"""


class NumberNode(object):
    def __init__(self, tok):
        self.tok = tok

    def __repr__(self):
        return f'{self.tok}'


"""
二元操作结点 + - * /  1 + 2  left_node：1，op_tok：+，right_node：2
"""


class BinOpNode(object):
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

    def __repr__(self):
        return f'{self.left_node}, {self.op_tok}, {self.right_node}'


"""
一元操作结点 -1 op_tok：-，node：1
"""


class UnaryOpNode(object):
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node

    # 将对象转化为供解释器读取的形式
    def __repr__(self):
        return f'{self.op_tok}, {self.node}'


"""
语法解析结果类
"""


class ParserResult(object):
    def __init__(self):
        self.error = None
        self.node = None

    # 解析成功
    def success(self, node):
        self.node = node
        return self

    # 解析失败
    def failure(self, error):
        self.error = error
        return self

    # 存储解析的结果
    def register(self, res):
        if isinstance(res, ParserResult):
            if res.error:
                self.error = res.error
            return res.node
        return res


"""
语法解析器
"""


class Parser(object):
    # 接收词法解析后的结果 Tokens
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()  # 往下读取 Token

    # noinspection PyAttributeOutsideInit
    def advance(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '+' '-' '*' or '/' "
            ))
        return res

    def factor(self):
        """
        factor -> INT | FLOAT
               -> ( PLUS | MINUS ) factor
               -> LPAREN expr RPAREN
        :return:
        """

        res = ParserResult()  # 拿到语法解析的结果
        tok = self.current_tok

        # factor -> INT | FLOAT
        if tok.type in (TT_INT, TT_FLOAT):
            res.register(self.advance())
            return res.success(NumberNode(tok))

        # factor -> ( PLUS | MINUS ) factor
        elif tok.type in (TT_PLUS, TT_MINUS):
            res.register(self.advance())
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(tok, factor))

        elif tok.type == TT_LPAREN:
            res.register(self.advance())  # 获取下一个字符
            expr = res.register((self.expr()))
            if res.error:
                return res

            if self.current_tok.type == TT_RPAREN:
                res.register(self.advance())
                return res.success(expr)
            else:  # 报错
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')' "
                ))
        return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected int or float "
        ))

    # term -> factor (( MUL | DIY ) factor)*
    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    # expr -> term (( PLUS | MINUS ) term)*
    def expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    # 递归调用构建AST
    def bin_op(self, func, ops):
        res = ParserResult()
        left = res.register(func())
        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.register((self.advance()))
            right = res.register(func())
            left = BinOpNode(left, op_tok, right)
        return res.success(left)


"""
运行
"""


def run(fn, text):  # fn：从键盘输入的数据，text的来源，<stdin>
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    print(tokens)
    # 生成AST
    parser = Parser(tokens)
    ast = parser.parse()
    return ast.node, ast.error
