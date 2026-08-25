"""
Cruise Programming Language (cruise-lang)
Version: 0.4.0
Author: Manjas Anand
License: MIT
"""

import sys
import os
import re
import math
import json
import urllib.request
import urllib.parse
import tkinter as tk
from typing import List, Dict, Any, Union, Optional

# --- Optional PyTorch Engine Integration ---
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# ==========================================
# 1. ADVANCED LEXER 🔍
# ==========================================

class Token:
    def __init__(self, type_: str, value: Any, line: int):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

KEYWORDS = {
    "let", "be", "if", "else", "while", "times",
    "fn", "define", "return", "end", "import",
    "write", "fetch", "post"
}

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.tokens: List[Token] = []

    def error(self, msg: str):
        raise SyntaxError(f"[Cruise Lexer Error] Line {self.line}: {msg}")

    def peek(self, offset: int = 1) -> str:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else ''

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            ch = self.source[self.pos]

            if ch == '\n':
                self.tokens.append(Token("NEWLINE", "\n", self.line))
                self.line += 1
                self.pos += 1
            elif ch.isspace():
                self.pos += 1
            elif ch == '#':  # Comments
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.pos += 1
            elif ch.isdigit() or (ch == '.' and self.peek(0).isdigit()):
                self.tokens.append(self.read_number())
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self.read_identifier())
            elif ch in ('"', "'"):
                self.tokens.append(self.read_string(ch))
            elif ch in ("=", "!", ">", "<"):
                self.tokens.append(self.read_operator())
            elif ch in "+-*/%@":
                self.tokens.append(Token("OP", ch, self.line))
                self.pos += 1
            elif ch == '(':
                self.tokens.append(Token("LPAREN", "(", self.line))
                self.pos += 1
            elif ch == ')':
                self.tokens.append(Token("RPAREN", ")", self.line))
                self.pos += 1
            elif ch == '[':
                self.tokens.append(Token("LBRACK", "[", self.line))
                self.pos += 1
            elif ch == ']':
                self.tokens.append(Token("RBRACK", "]", self.line))
                self.pos += 1
            elif ch == ':':
                self.tokens.append(Token("COLON", ":", self.line))
                self.pos += 1
            elif ch == ',':
                self.tokens.append(Token("COMMA", ",", self.line))
                self.pos += 1
            else:
                self.error(f"Unexpected character '{ch}'")

        self.tokens.append(Token("EOF", None, self.line))
        return self.tokens

    def read_number(self) -> Token:
        num_str = ""
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            num_str += self.source[self.pos]
            self.pos += 1
        val = float(num_str) if '.' in num_str else int(num_str)
        return Token("NUMBER", val, self.line)

    def read_identifier(self) -> Token:
        ident = ""
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            ident += self.source[self.pos]
            self.pos += 1
        type_ = "KEYWORD" if ident in KEYWORDS else "IDENT"
        return Token(type_, ident, self.line)

    def read_string(self, quote: str) -> Token:
        self.pos += 1  # Skip opening quote
        str_val = ""
        while self.pos < len(self.source) and self.source[self.pos] != quote:
            if self.source[self.pos] == '\\' and self.pos + 1 < len(self.source):
                self.pos += 1
                esc = self.source[self.pos]
                str_val += {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', '"': '"', "'": "'"}.get(esc, esc)
            else:
                str_val += self.source[self.pos]
            self.pos += 1
        self.pos += 1  # Skip closing quote
        return Token("STRING", str_val, self.line)

    def read_operator(self) -> Token:
        ch = self.source[self.pos]
        self.pos += 1
        if self.pos < len(self.source) and self.source[self.pos] == '=':
            op = ch + '='
            self.pos += 1
            return Token("OP", op, self.line)
        return Token("ASSIGN" if ch == '=' else "OP", ch, self.line)


# ==========================================
# 2. ABSTRACT SYNTAX TREE (AST) PARSER 🌳
# ==========================================

class ASTNode: pass

class NumberNode(ASTNode):
    def __init__(self, val): self.val = val
class StringNode(ASTNode):
    def __init__(self, val): self.val = val
class VarNode(ASTNode):
    def __init__(self, name): self.name = name
class ListNode(ASTNode):
    def __init__(self, elements): self.elements = elements
class AssignNode(ASTNode):
    def __init__(self, name, expr): self.name = name; self.expr = expr
class BinOpNode(ASTNode):
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right
class CallNode(ASTNode):
    def __init__(self, callee, args): self.callee = callee; self.args = args
class IndexNode(ASTNode):
    def __init__(self, target, index): self.target = target; self.index = index
class IfNode(ASTNode):
    def __init__(self, cond, then_block, else_block=None): self.cond = cond; self.then_block = then_block; self.else_block = else_block
class WhileNode(ASTNode):
    def __init__(self, cond, body): self.cond = cond; self.body = body
class TimesNode(ASTNode):
    def __init__(self, count_expr, stmt): self.count_expr = count_expr; self.stmt = stmt
class FuncNode(ASTNode):
    def __init__(self, name, params, body): self.name = name; self.params = params; self.body = body
class ReturnNode(ASTNode):
    def __init__(self, expr): self.expr = expr
class ImportNode(ASTNode):
    def __init__(self, module_name): self.module_name = module_name


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def error(self, msg: str):
        tok = self.current()
        raise SyntaxError(f"[Cruise Parser Error] Line {tok.line}: {msg} at '{tok.value}'")

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek_next(self) -> Token:
        return self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else self.tokens[-1]

    def eat(self, type_: str, value: Any = None) -> Token:
        tok = self.current()
        if tok.type == type_ and (value is None or tok.value == value):
            self.pos += 1
            return tok
        self.error(f"Expected {type_} ({value}), got {tok.type} ({tok.value})")

    def skip_newlines(self):
        while self.current().type == "NEWLINE":
            self.pos += 1

    def parse(self) -> List[ASTNode]:
        statements = []
        while self.current().type != "EOF":
            self.skip_newlines()
            if self.current().type == "EOF":
                break
            statements.append(self.statement())
            self.skip_newlines()
        return statements

    def statement(self) -> ASTNode:
        tok = self.current()

        # 1. let x = expr OR let x be expr
        if tok.type == "KEYWORD" and tok.value == "let":
            self.eat("KEYWORD", "let")
            name = self.eat("IDENT").value
            if self.current().type == "KEYWORD" and self.current().value == "be":
                self.eat("KEYWORD", "be")
            else:
                self.eat("ASSIGN")
            expr = self.expr()
            return AssignNode(name, expr)

        # 2. if statement
        if tok.type == "KEYWORD" and tok.value == "if":
            return self.if_statement()

        # 3. while statement
        if tok.type == "KEYWORD" and tok.value == "while":
            return self.while_statement()

        # 4. fn / define statement
        if tok.type == "KEYWORD" and tok.value in ("fn", "define"):
            return self.func_def()

        # 5. return statement
        if tok.type == "KEYWORD" and tok.value == "return":
            self.eat("KEYWORD", "return")
            return ReturnNode(self.expr())

        # 6. import statement
        if tok.type == "KEYWORD" and tok.value == "import":
            self.eat("KEYWORD", "import")
            mod_name = self.eat("IDENT").value
            return ImportNode(mod_name)

        # 7. write statement
        if tok.type == "KEYWORD" and tok.value == "write":
            self.eat("KEYWORD", "write")
            if self.current().type == "LPAREN":
                self.eat("LPAREN")
                arg = self.expr()
                self.eat("RPAREN")
            else:
                arg = self.expr()
            return CallNode("write", [arg])

        # 8. Direct assignment: x = expr
        if tok.type == "IDENT" and self.peek_next().type == "ASSIGN":
            name = self.eat("IDENT").value
            self.eat("ASSIGN")
            return AssignNode(name, self.expr())

        # 9. Times automation: N times <stmt>
        left_expr = self.expr()
        if self.current().type == "KEYWORD" and self.current().value == "times":
            self.eat("KEYWORD", "times")
            body_stmt = self.statement()
            return TimesNode(left_expr, body_stmt)

        return left_expr

    def if_statement(self) -> IfNode:
        self.eat("KEYWORD", "if")
        cond = self.expr()
        if self.current().type == "COLON":
            self.eat("COLON")
        then_block = []
        self.skip_newlines()

        while not (self.current().type == "KEYWORD" and self.current().value in ("else", "end")):
            then_block.append(self.statement())
            self.skip_newlines()

        else_block = None
        if self.current().type == "KEYWORD" and self.current().value == "else":
            self.eat("KEYWORD", "else")
            if self.current().type == "COLON":
                self.eat("COLON")
            self.skip_newlines()
            else_block = []
            while not (self.current().type == "KEYWORD" and self.current().value == "end"):
                else_block.append(self.statement())
                self.skip_newlines()

        self.eat("KEYWORD", "end")
        return IfNode(cond, then_block, else_block)

    def while_statement(self) -> WhileNode:
        self.eat("KEYWORD", "while")
        cond = self.expr()
        if self.current().type == "COLON":
            self.eat("COLON")
        body = []
        self.skip_newlines()
        while not (self.current().type == "KEYWORD" and self.current().value == "end"):
            body.append(self.statement())
            self.skip_newlines()
        self.eat("KEYWORD", "end")
        return WhileNode(cond, body)

    def func_def(self) -> FuncNode:
        kw = self.eat("KEYWORD").value  # 'fn' or 'define'
        name = self.eat("IDENT").value
        self.eat("LPAREN")
        params = []
        if self.current().type == "IDENT":
            params.append(self.eat("IDENT").value)
            while self.current().type == "COMMA":
                self.eat("COMMA")
                params.append(self.eat("IDENT").value)
        self.eat("RPAREN")
        if self.current().type == "COLON":
            self.eat("COLON")
        body = []
        self.skip_newlines()
        while not (self.current().type == "KEYWORD" and self.current().value == "end"):
            body.append(self.statement())
            self.skip_newlines()
        self.eat("KEYWORD", "end")
        return FuncNode(name, params, body)

    def expr(self) -> ASTNode:
        left = self.comp_expr()
        while self.current().type == "OP" and self.current().value in ("==", "!=", "<", ">", "<=", ">="):
            op = self.eat("OP").value
            right = self.comp_expr()
            left = BinOpNode(left, op, right)
        return left

    def comp_expr(self) -> ASTNode:
        left = self.term()
        while self.current().type == "OP" and self.current().value in ("+", "-"):
            op = self.eat("OP").value
            right = self.term()
            left = BinOpNode(left, op, right)
        return left

    def term(self) -> ASTNode:
        left = self.factor()
        while self.current().type == "OP" and self.current().value in ("*", "/", "%", "@"):
            op = self.eat("OP").value
            right = self.factor()
            left = BinOpNode(left, op, right)
        return left

    def factor(self) -> ASTNode:
        tok = self.current()

        if tok.type == "NUMBER":
            self.eat("NUMBER")
            node = NumberNode(tok.value)
        elif tok.type == "STRING":
            self.eat("STRING")
            node = StringNode(tok.value)
        elif tok.type == "IDENT" or (tok.type == "KEYWORD" and tok.value in ("fetch", "post")):
            name = self.eat(tok.type).value
            if self.current().type == "LPAREN":
                self.eat("LPAREN")
                args = []
                if self.current().type != "RPAREN":
                    args.append(self.expr())
                    while self.current().type == "COMMA":
                        self.eat("COMMA")
                        args.append(self.expr())
                self.eat("RPAREN")
                node = CallNode(name, args)
            else:
                node = VarNode(name)
        elif tok.type == "LBRACK":
            self.eat("LBRACK")
            elements = []
            if self.current().type != "RBRACK":
                elements.append(self.expr())
                while self.current().type == "COMMA":
                    self.eat("COMMA")
                    elements.append(self.expr())
            self.eat("RBRACK")
            node = ListNode(elements)
        elif tok.type == "LPAREN":
            self.eat("LPAREN")
            node = self.expr()
            self.eat("RPAREN")
        else:
            self.error(f"Unexpected token in expression: {tok.value}")

        # Postfix bracket indexing: arr[0]
        while self.current().type == "LBRACK":
            self.eat("LBRACK")
            idx = self.expr()
            self.eat("RBRACK")
            node = IndexNode(node, idx)

        return node


# ==========================================
# 3. INTERPRETER & ENVIRONMENT 🧠
# ==========================================

class ReturnException(Exception):
    def __init__(self, value): self.value = value

class Environment:
    def __init__(self, parent=None):
        self.vars: Dict[str, Any] = {}
        self.parent = parent

    def get(self, name: str) -> Any:
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"[Cruise Engine] Variable '{name}' is not defined.")

    def set(self, name: str, val: Any):
        self.vars[name] = val


class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self._setup_builtins()

    def _setup_builtins(self):
        # 1. Standard Output
        self.global_env.set("write", lambda *args: print(*args))
        self.global_env.set("print", lambda *args: print(*args))

        # 2. Math Library 📐
        self.global_env.set("sin", math.sin)
        self.global_env.set("cos", math.cos)
        self.global_env.set("tan", math.tan)
        self.global_env.set("sqrt", math.sqrt)
        self.global_env.set("log", math.log)
        self.global_env.set("exp", math.exp)
        self.global_env.set("abs", abs)
        self.global_env.set("round", round)
        self.global_env.set("pi", math.pi)
        self.global_env.set("e", math.e)

        # 3. HTTP Network Suite 🌐
        self.global_env.set("fetch", self._fetch_url)
        self.global_env.set("post", self._post_url)

        # 4. PyTorch Deep Learning & Tensor Calculus 🧠
        if TORCH_AVAILABLE:
            self.global_env.set("tensor", lambda data, req_grad=False: torch.tensor(data, dtype=torch.float32, requires_grad=req_grad))
            self.global_env.set("grad", lambda t: t.grad if hasattr(t, 'grad') else None)
            self.global_env.set("backward", lambda t: t.backward() if hasattr(t, 'backward') else None)
            self.global_env.set("zero_grad", lambda opt: opt.zero_grad())
            self.global_env.set("step", lambda opt: opt.step())
            self.global_env.set("opt_sgd", lambda params, lr=0.01: torch.optim.SGD(params, lr=lr))
            self.global_env.set("opt_adam", lambda params, lr=0.001: torch.optim.Adam(params, lr=lr))
            self.global_env.set("relu", lambda t: torch.relu(t) if TORCH_AVAILABLE else None)
            self.global_env.set("sigmoid", lambda t: torch.sigmoid(t) if TORCH_AVAILABLE else None)
            self.global_env.set("mse_loss", lambda y_pred, y_true: torch.nn.functional.mse_loss(y_pred, y_true))
        else:
            self.global_env.set("tensor", lambda data, req_grad=False: data)

        # 5. GUI Framework 🖼️
        self.global_env.set("gui_window", self._gui_window)
        self.global_env.set("background", lambda color: print(f"[Cruise GUI] Theme set to: {color}"))
        self.global_env.set("button", lambda text: print(f"[Cruise GUI] Button rendered: [{text}]"))

    def _fetch_url(self, url: str) -> Any:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Cruise-Lang/0.4.0'})
            with urllib.request.urlopen(req) as res:
                content = res.read().decode('utf-8')
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return content
        except Exception as e:
            return f"[Cruise HTTP Error] {e}"

    def _post_url(self, url: str, data: Any) -> Any:
        try:
            encoded_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=encoded_data, headers={'Content-Type': 'application/json', 'User-Agent': 'Cruise-Lang/0.4.0'})
            with urllib.request.urlopen(req) as res:
                return res.read().decode('utf-8')
        except Exception as e:
            return f"[Cruise HTTP Error] {e}"

    def _gui_window(self, title: str, btn_text: str, callback):
        try:
            root = tk.Tk()
            root.title(title)
            root.geometry("320x180")
            lbl = tk.Label(root, text=title, font=("Helvetica", 12, "bold"))
            lbl.pack(pady=15)
            btn = tk.Button(root, text=btn_text, command=lambda: callback(), bg="#0ea5e9", fg="white", font=("Helvetica", 10, "bold"), padx=10, pady=5)
            btn.pack(pady=10)
            root.mainloop()
        except Exception as e:
            print(f"[Cruise GUI Headless] {title} -> Button '{btn_text}' triggered (GUI unavailable: {e})")
            callback()

    def eval(self, node: ASTNode, env: Environment) -> Any:
        if isinstance(node, NumberNode):
            return node.val
        elif isinstance(node, StringNode):
            return node.val
        elif isinstance(node, ListNode):
            return [self.eval(elem, env) for elem in node.elements]
        elif isinstance(node, VarNode):
            return env.get(node.name)
        elif isinstance(node, AssignNode):
            val = self.eval(node.expr, env)
            env.set(node.name, val)
            return val
        elif isinstance(node, IndexNode):
            target = self.eval(node.target, env)
            idx = self.eval(node.index, env)
            return target[idx]
        elif isinstance(node, BinOpNode):
            left = self.eval(node.left, env)
            right = self.eval(node.right, env)
            if node.op == '+': return left + right
            elif node.op == '-': return left - right
            elif node.op == '*': return left * right
            elif node.op == '/': return left / right
            elif node.op == '%': return left % right
            elif node.op == '@':
                if TORCH_AVAILABLE and isinstance(left, torch.Tensor):
                    return torch.matmul(left, right)
                return left @ right
            elif node.op == '==': return left == right
            elif node.op == '!=': return left != right
            elif node.op == '<': return left < right
            elif node.op == '>': return left > right
            elif node.op == '<=': return left <= right
            elif node.op == '>=': return left >= right
        elif isinstance(node, CallNode):
            fn = env.get(node.callee) if isinstance(node.callee, str) else self.eval(node.callee, env)
            args = [self.eval(arg, env) for arg in node.args]
            if callable(fn):
                return fn(*args)
            elif isinstance(fn, FuncNode):
                local_env = Environment(parent=env)
                for param, arg in zip(fn.params, args):
                    local_env.set(param, arg)
                try:
                    for stmt in fn.body:
                        self.eval(stmt, local_env)
                except ReturnException as ret:
                    return ret.value
                return None
            else:
                raise TypeError(f"'{node.callee}' is not callable.")
        elif isinstance(node, IfNode):
            if self.eval(node.cond, env):
                res = None
                for stmt in node.then_block:
                    res = self.eval(stmt, env)
                return res
            elif node.else_block:
                res = None
                for stmt in node.else_block:
                    res = self.eval(stmt, env)
                return res
        elif isinstance(node, WhileNode):
            res = None
            while self.eval(node.cond, env):
                for stmt in node.body:
                    res = self.eval(stmt, env)
            return res
        elif isinstance(node, TimesNode):
            count = int(self.eval(node.count_expr, env))
            res = None
            for _ in range(count):
                res = self.eval(node.stmt, env)
            return res
        elif isinstance(node, FuncNode):
            env.set(node.name, node)
            return node
        elif isinstance(node, ReturnNode):
            raise ReturnException(self.eval(node.expr, env))
        elif isinstance(node, ImportNode):
            self._import_module(node.module_name, env)

    def _import_module(self, mod_name: str, env: Environment):
        file_path = f"{mod_name}.cru"
        if not os.path.exists(file_path):
            file_path = f"{mod_name}.crui"
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"[Cruise Import Error] Module '{mod_name}' not found (.cru/.crui).")
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        lexer = Lexer(code)
        parser = Parser(lexer.tokenize())
        for node in parser.parse():
            self.eval(node, env)


# ==========================================
# 4. CRUISE PACKAGE MANAGER (CPM) 📦
# ==========================================

def cruise_package_manager(cmd: str, pkg_name: str):
    if cmd == "install":
        print(f"📦 [CPM] Fetching package '{pkg_name}'...")
        try:
            content = f"# Cruise Package: {pkg_name}\nfn {pkg_name}_info():\n    write('{pkg_name} package loaded successfully!')\nend\n"
            with open(f"{pkg_name}.cru", "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ [CPM] Successfully installed '{pkg_name}' ({pkg_name}.cru)!")
        except Exception as e:
            print(f"❌ [CPM] Package install failed: {e}")


# ==========================================
# 5. CLI & REPL ENTRY POINT 🚀
# ==========================================

def main():
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]

        # CPM subcommands
        if arg1 == "install" and len(sys.argv) > 2:
            cruise_package_manager("install", sys.argv[2])
            return

        # Execute standalone script
        if os.path.exists(arg1):
            with open(arg1, "r", encoding="utf-8") as f:
                code = f.read()
            interpreter = Interpreter()
            lexer = Lexer(code)
            parser = Parser(lexer.tokenize())
            for node in parser.parse():
                interpreter.eval(node, interpreter.global_env)
        else:
            print(f"❌ File '{arg1}' not found.")
    else:
        # Interactive REPL shell
        print("🚢 Cruise Language REPL v0.4.0 Engine")
        print("Created with ❤️ by Manjas Anand | Type 'exit()' to close.\n")
        interpreter = Interpreter()
        while True:
            try:
                line = input("cruise> ")
                if line.strip() in ("exit()", "quit()"):
                    break
                if not line.strip():
                    continue
                lexer = Lexer(line)
                parser = Parser(lexer.tokenize())
                for node in parser.parse():
                    res = interpreter.eval(node, interpreter.global_env)
                    if res is not None:
                        print(res)
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
