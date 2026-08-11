import sys
import os
import re
import math
import urllib.request
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
    "let", "if", "else", "while", "fn", "return", 
    "import", "tensor", "write", "gui", "opt"
}

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.tokens: List[Token] = []

    def error(self, msg: str):
        raise SyntaxError(f"[Cruise Lexer Error] Line {self.line}: {msg}")

    def tokenize(self) -> List[Token]:
        while self.pos < len(self.source):
            ch = self.source[self.pos]

            if ch == '\n':
                self.line += 1
                self.tokens.append(Token("NEWLINE", "\n", self.line))
                self.pos += 1
            elif ch.isspace():
                self.pos += 1
            elif ch == '#':  # Comments
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.pos += 1
            elif ch.isdigit() or (ch == '.' and self.peek().isdigit()):
                self.tokens.append(self.read_number())
            elif ch.isalpha() or ch == '_':
                self.tokens.append(self.read_identifier())
            elif ch in ('"', "'"):
                self.tokens.append(self.read_string(ch))
            elif ch in ("=", "!", ">", "<"):
                self.tokens.append(self.read_operator())
            elif ch in "+-*/%":
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

    def peek(self) -> str:
        return self.source[self.pos + 1] if self.pos + 1 < len(self.source) else ''

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
        self.pos += 1 # skip opening quote
        str_val = ""
        while self.pos < len(self.source) and self.source[self.pos] != quote:
            str_val += self.source[self.pos]
            self.pos += 1
        self.pos += 1 # skip closing quote
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
class IfNode(ASTNode):
    def __init__(self, cond, then_block, else_block=None): self.cond = cond; self.then_block = then_block; self.else_block = else_block
class WhileNode(ASTNode):
    def __init__(self, cond, body): self.cond = cond; self.body = body
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
            if self.current().type == "EOF": break
            statements.append(self.statement())
            self.skip_newlines()
        return statements

    def statement(self) -> ASTNode:
        tok = self.current()
        
        if tok.type == "KEYWORD":
            if tok.value == "let":
                self.eat("KEYWORD", "let")
                name = self.eat("IDENT").value
                self.eat("ASSIGN")
                expr = self.expr()
                return AssignNode(name, expr)
            elif tok.value == "if":
                return self.if_statement()
            elif tok.value == "while":
                return self.while_statement()
            elif tok.value == "fn":
                return self.func_def()
            elif tok.value == "return":
                self.eat("KEYWORD", "return")
                return ReturnNode(self.expr())
            elif tok.value == "import":
                self.eat("KEYWORD", "import")
                mod_name = self.eat("IDENT").value
                return ImportNode(mod_name)
            elif tok.value == "write":
                self.eat("KEYWORD", "write")
                return CallNode("write", [self.expr()])

        # Handle simple assignment: x = expr (Support single '=' flexibility)
        if tok.type == "IDENT" and self.peek_type() == "ASSIGN":
            name = self.eat("IDENT").value
            self.eat("ASSIGN")
            return AssignNode(name, self.expr())

        return self.expr()

    def peek_type(self) -> str:
        return self.tokens[self.pos + 1].type if self.pos + 1 < len(self.tokens) else "EOF"

    def if_statement() -> IfNode:
        self.eat("KEYWORD", "if")
        cond = self.expr()
        self.eat("COLON")
        then_block = []
        self.skip_newlines()
        
        while not (self.current().type == "KEYWORD" and self.current().value in ("else", "end")):
            then_block.append(self.statement())
            self.skip_newlines()

        else_block = None
        if self.current().type == "KEYWORD" and self.current().value == "else":
            self.eat("KEYWORD", "else")
            self.eat("COLON")
            self.skip_newlines()
            else_block = []
            while not (self.current().type == "KEYWORD" and self.current().value == "end"):
                else_block.append(self.statement())
                self.skip_newlines()

        self.eat("KEYWORD", "end")
        return IfNode(cond, then_block, else_block)

    def while_statement() -> WhileNode:
        self.eat("KEYWORD", "while")
        cond = self.expr()
        self.eat("COLON")
        body = []
        self.skip_newlines()
        while not (self.current().type == "KEYWORD" and self.current().value == "end"):
            body.append(self.statement())
            self.skip_newlines()
        self.eat("KEYWORD", "end")
        return WhileNode(cond, body)

    def func_def() -> FuncNode:
        self.eat("KEYWORD", "fn")
        name = self.eat("IDENT").value
        self.eat("LPAREN")
        params = []
        if self.current().type == "IDENT":
            params.append(self.eat("IDENT").value)
            while self.current().type == "COMMA":
                self.eat("COMMA")
                params.append(self.eat("IDENT").value)
        self.eat("RPAREN")
        self.eat("COLON")
        body = []
        self.skip_newlines()
        while not (self.current().type == "KEYWORD" and self.current().value == "end"):
            body.append(self.statement())
            self.skip_newlines()
        self.eat("KEYWORD", "end")
        return FuncNode(name, params, body)

    def expr() -> ASTNode:
        left = self.comp_expr()
        while self.current().type == "OP" and self.current().value in ("==", "!=", "<", ">", "<=", ">="):
            op = self.eat("OP").value
            right = self.comp_expr()
            left = BinOpNode(left, op, right)
        return left

    def comp_expr() -> ASTNode:
        left = self.term()
        while self.current().type == "OP" and self.current().value in ("+", "-"):
            op = self.eat("OP").value
            right = self.term()
            left = BinOpNode(left, op, right)
        return left

    def term() -> ASTNode:
        left = self.factor()
        while self.current().type == "OP" and self.current().value in ("*", "/", "%"):
            op = self.eat("OP").value
            right = self.factor()
            left = BinOpNode(left, op, right)
        return left

    def factor() -> ASTNode:
        tok = self.current()
        if tok.type == "NUMBER":
            self.eat("NUMBER")
            return NumberNode(tok.value)
        elif tok.type == "STRING":
            self.eat("STRING")
            return StringNode(tok.value)
        elif tok.type == "IDENT":
            name = self.eat("IDENT").value
            if self.current().type == "LPAREN":
                self.eat("LPAREN")
                args = []
                if self.current().type != "RPAREN":
                    args.append(self.expr())
                    while self.current().type == "COMMA":
                        self.eat("COMMA")
                        args.append(self.expr())
                self.eat("RPAREN")
                return CallNode(name, args)
            return VarNode(name)
        elif tok.type == "LBRACK":
            self.eat("LBRACK")
            elements = []
            if self.current().type != "RBRACK":
                elements.append(self.expr())
                while self.current().type == "COMMA":
                    self.eat("COMMA")
                    elements.append(self.expr())
            self.eat("RBRACK")
            return ListNode(elements)
        elif tok.type == "LPAREN":
            self.eat("LPAREN")
            node = self.expr()
            self.eat("RPAREN")
            return node
        self.error("Unexpected factor expression")


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
        # Write / Print
        self.global_env.set("write", print)
        
        # Math Library 📐
        self.global_env.set("sin", math.sin)
        self.global_env.set("cos", math.cos)
        self.global_env.set("sqrt", math.sqrt)
        self.global_env.set("pi", math.pi)

        # PyTorch Tensor Calculus & Optimizers 🧠
        if TORCH_AVAILABLE:
            self.global_env.set("tensor", lambda data, req_grad=False: torch.tensor(data, dtype=torch.float32, requires_grad=req_grad))
            self.global_env.set("grad", lambda t: t.grad)
            self.global_env.set("backward", lambda t: t.backward())
            self.global_env.set("opt_sgd", lambda params, lr=0.01: torch.optim.SGD(params, lr=lr))
            self.global_env.set("opt_adam", lambda params, lr=0.001: torch.optim.Adam(params, lr=lr))

        # GUI Framework 🖼️
        self.global_env.set("gui_window", self._gui_window)

    def _gui_window(self, title: str, btn_text: str, callback):
        root = tk.Tk()
        root.title(title)
        root.geometry("300x150")
        lbl = tk.Label(root, text=title, font=("Arial", 12))
        lbl.pack(pady=10)
        btn = tk.Button(root, text=btn_text, command=lambda: callback(), bg="#4CAF50", fg="white")
        btn.pack(pady=10)
        root.mainloop()

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
        elif isinstance(node, BinOpNode):
            left = self.eval(node.left, env)
            right = self.eval(node.right, env)
            if node.op == '+': return left + right
            elif node.op == '-': return left - right
            elif node.op == '*': return left * right
            elif node.op == '/': return left / right
            elif node.op == '==': return left == right
            elif node.op == '!=': return left != right
            elif node.op == '<': return left < right
            elif node.op == '>': return left > right
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
        elif isinstance(node, IfNode):
            if self.eval(node.cond, env):
                for stmt in node.then_block: self.eval(stmt, env)
            elif node.else_block:
                for stmt in node.else_block: self.eval(stmt, env)
        elif isinstance(node, WhileNode):
            while self.eval(node.cond, env):
                for stmt in node.body: self.eval(stmt, env)
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
            raise FileNotFoundError(f"[Cruise Import Error] Cannot find module '{file_path}'")
        with open(file_path, "r") as f:
            code = f.read()
        lexer = Lexer(code)
        parser = Parser(lexer.tokenize())
        nodes = parser.parse()
        for node in nodes:
            self.eval(node, env)


# ==========================================
# 4. CRUISE PACKAGE MANAGER (CPM) 📦
# ==========================================

def cruise_package_manager(cmd: str, pkg_name: str):
    if cmd == "install":
        print(f"📦 [CPM] Fetching package '{pkg_name}'...")
        # Simulated package installer fetching module template
        url = f"https://raw.githubusercontent.com/manjas-developer/cruise-packages/main/{pkg_name}.cru"
        try:
            content = f"# Package: {pkg_name}\nfn {pkg_name}_hello():\n  write('{pkg_name} initialized!')\nend\n"
            with open(f"{pkg_name}.cru", "w") as f:
                f.write(content)
            print(f"✅ [CPM] Successfully installed '{pkg_name}' into workspace!")
        except Exception as e:
            print(f"❌ [CPM] Failed to install package: {e}")


# ==========================================
# 5. CLI & REPL ENTRY POINT 🚀
# ==========================================

def main():
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        
        # Package Manager Subcommand
        if arg1 == "install" and len(sys.argv) > 2:
            cruise_package_manager("install", sys.argv[2])
            return

        # Execute File
        if os.path.exists(arg1):
            with open(arg1, "r") as f:
                code = f.read()
            interpreter = Interpreter()
            lexer = Lexer(code)
            parser = Parser(lexer.tokenize())
            ast_nodes = parser.parse()
            for node in ast_nodes:
                interpreter.eval(node, interpreter.global_env)
        else:
            print(f"File '{arg1}' not found.")
    else:
        # REPL Mode
        print("🚢 Cruise Language REPL v0.3.0 Engine")
        print("Type 'exit()' to close.\n")
        interpreter = Interpreter()
        while True:
            try:
                line = input("cruise> ")
                if line.strip() == "exit()": break
                if not line.strip(): continue
                lexer = Lexer(line)
                parser = Parser(lexer.tokenize())
                nodes = parser.parse()
                for node in nodes:
                    res = interpreter.eval(node, interpreter.global_env)
                    if res is not None: print(res)
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
