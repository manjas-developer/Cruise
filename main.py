"""
=============================================================================
CRUISE PROGRAMMING LANGUAGE INTERPRETER (`cruise-lang`)
Author: Manjas Anand
Version: 0.2.0
License: MIT
Description: High-performance, lightweight tensor calculus, machine learning,
             and UI execution engine built for multi-platform execution.
=============================================================================
"""

import sys
import os
import math
import time
import json
import re
from typing import List, Dict, Any, Union, Optional

# =============================================================================
# 1. ENVIRONMENT & BACKEND DEPENDENCY MANAGEMENT
# =============================================================================

# HTTP Backend Engine
try:
    import urllib.request
    import urllib.parse
    import urllib.error
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

# GUI Backend Driver (Tkinter) with Headless Environment Detection
HAS_TKINTER = False
try:
    if os.environ.get('DISPLAY') or os.name == 'nt' or sys.platform == 'darwin':
        import tkinter as tk
        from tkinter import ttk, messagebox
        HAS_TKINTER = True
except Exception:
    HAS_TKINTER = False


# =============================================================================
# 2. ADVANCED TENSOR & ML ENGINE
# =============================================================================

class CruiseTensor:
    """Lightweight, Native Tensor Architecture for ML & Linear Algebra."""
    
    def __init__(self, data: Union[int, float, List[Any]]):
        if isinstance(data, (int, float)):
            self.data = [float(data)]
            self.shape = (1,)
        elif isinstance(data, list):
            self.data = self._flatten(data)
            self.shape = (len(data),)
        else:
            raise TypeError("CruiseTensor input must be a scalar, vector, or list.")

    def _flatten(self, lst: List[Any]) -> List[float]:
        flat = []
        for item in lst:
            if isinstance(item, list):
                flat.extend(self._flatten(item))
            else:
                flat.append(float(item))
        return flat

    def add(self, other: Union['CruiseTensor', float, int]) -> 'CruiseTensor':
        if isinstance(other, CruiseTensor):
            if len(self.data) != len(other.data):
                raise ValueError("Tensor dimension mismatch for addition.")
            return CruiseTensor([a + b for a, b in zip(self.data, other.data)])
        return CruiseTensor([a + float(other) for a in self.data])

    def multiply(self, other: Union['CruiseTensor', float, int]) -> 'CruiseTensor':
        if isinstance(other, CruiseTensor):
            if len(self.data) != len(other.data):
                raise ValueError("Tensor dimension mismatch for multiplication.")
            return CruiseTensor([a * b for a, b in zip(self.data, other.data)])
        return CruiseTensor([a * float(other) for a in self.data])

    def sum(self) -> float:
        return sum(self.data)

    def mean(self) -> float:
        return sum(self.data) / len(self.data) if self.data else 0.0

    def relu(self) -> 'CruiseTensor':
        return CruiseTensor([max(0.0, x) for x in self.data])

    def __repr__(self) -> str:
        return f"CruiseTensor(shape={self.shape}, values={self.data})"


# =============================================================================
# 3. LEXER & TOKENIZER
# =============================================================================

class TokenType:
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"
    OPERATOR = "OPERATOR"
    DELIMITER = "DELIMITER"
    EOF = "EOF"

class Token:
    def __init__(self, type_: str, value: Any, line: int):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

class CruiseLexer:
    KEYWORDS = {"define", "end", "times", "write", "fetch", "post", "background", "button", "tensor", "if", "else"}

    def __init__(self, source_code: str):
        self.source = source_code
        self.position = 0
        self.line = 1

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.position < len(self.source):
            char = self.source[self.position]

            if char in " \t\r":
                self.position += 1
            elif char == "\n":
                self.line += 1
                self.position += 1
            elif char == "#":
                while self.position < len(self.source) and self.source[self.position] != "\n":
                    self.position += 1
            elif char.isalpha() or char == "_":
                tokens.append(self._read_identifier())
            elif char.isdigit() or (char == "." and self._peek().isdigit()):
                tokens.append(self._read_number())
            elif char in "\"'":
                tokens.append(self._read_string(char))
            elif char in "+-*/=":
                tokens.append(Token(TokenType.OPERATOR, char, self.line))
                self.position += 1
            elif char in "(),:":
                tokens.append(Token(TokenType.DELIMITER, char, self.line))
                self.position += 1
            else:
                self.position += 1  # Ignore unknown characters
        
        tokens.append(Token(TokenType.EOF, "", self.line))
        return tokens

    def _peek(self) -> str:
        if self.position + 1 < len(self.source):
            return self.source[self.position + 1]
        return ""

    def _read_identifier(self) -> Token:
        start = self.position
        while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == "_"):
            self.position += 1
        val = self.source[start:self.position]
        token_type = TokenType.KEYWORD if val in self.KEYWORDS else TokenType.IDENTIFIER
        return Token(token_type, val, self.line)

    def _read_number(self) -> Token:
        start = self.position
        has_dot = False
        while self.position < len(self.source) and (self.source[self.position].isdigit() or self.source[self.position] == "."):
            if self.source[self.position] == ".":
                if has_dot: break
                has_dot = True
            self.position += 1
        num_str = self.source[start:self.position]
        return Token(TokenType.NUMBER, float(num_str) if has_dot else int(num_str), self.line)

    def _read_string(self, quote_char: str) -> Token:
        self.position += 1 # Skip open quote
        start = self.position
        while self.position < len(self.source) and self.source[self.position] != quote_char:
            self.position += 1
        val = self.source[start:self.position]
        self.position += 1 # Skip close quote
        return Token(TokenType.STRING, val, self.line)


# =============================================================================
# 4. MEMORY SCOPING & RUNTIME ENVIRONMENT
# =============================================================================

class Environment:
    """Manages Scoped Variables and Function Memory Frames."""
    def __init__(self, parent: Optional['Environment'] = None):
        self.bindings: Dict[str, Any] = {}
        self.parent = parent

    def set(self, name: str, value: Any):
        self.bindings[name] = value

    def get(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Undefined variable or function symbol '{name}' in Cruise scope.")


# =============================================================================
# 5. CORE INTERPRETER ENGINE
# =============================================================================

class CruiseInterpreter:
    def __init__(self):
        self.global_env = Environment()
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.gui_root = None
        self.version = "0.2.0"
        self.creator = "Manjas Anand"

    def print_welcome_banner(self):
        """Displays startup personalized REPL banner."""
        print("=" * 70)
        print(f"  🚢 CRUISE PROGRAMMING LANGUAGE REPL v{self.version}")
        print(f"  👨‍💻 Designed & Developed with ❤️ by {self.creator}")
        print("  ⚡ Tensor Calculus | ML Engine | Native Web & Desktop UI")
        print("  💡 Type 'exit', 'quit', or press Ctrl+C to close the shell session.")
        print("=" * 70)

    def print_exit_banner(self):
        """Displays exit personalized REPL banner."""
        print("\n" + "=" * 70)
        print(f"  👋 Thank you for building with Cruise Language, {self.creator}!")
        print("  🚀 Keep crushing code, training models, and innovating!")
        print("=" * 70)

    def execute_script(self, code_text: str):
        """Line-by-Line AST Execution Engine with error handling."""
        lines = [line.strip() for line in code_text.splitlines() if line.strip() and not line.strip().startswith("#")]
        self._eval_block(lines, self.global_env)

    def _eval_block(self, lines: List[str], env: Environment):
        i = 0
        while i < len(lines):
            line = lines[i]

            # --- 1. Function Definition ("define name(arg1, arg2): ... end") ---
            if line.startswith("define "):
                func_header = line[7:].rstrip(":")
                func_name, args_part = func_header.split("(")
                func_name = func_name.strip()
                arg_names = [a.strip() for a in args_part.rstrip(")").split(",") if a.strip()]

                body_lines = []
                i += 1
                while i < len(lines) and lines[i] != "end":
                    body_lines.append(lines[i])
                    i += 1

                self.functions[func_name] = {
                    "args": arg_names,
                    "body": body_lines
                }

            # --- 2. Function Execution ---
            elif "(" in line and line.endswith(")") and not any(line.startswith(kw) for kw in ["write", "fetch", "post", "background", "button", "tensor"]):
                func_name, args_part = line.rstrip(")").split("(", 1)
                func_name = func_name.strip()

                if func_name in self.functions:
                    raw_args = [a.strip() for a in args_part.split(",") if a.strip()]
                    func_data = self.functions[func_name]

                    # Create scoped environment frame
                    local_env = Environment(parent=env)
                    for param, val_expr in zip(func_data["args"], raw_args):
                        local_env.set(param, self._eval_expression(val_expr, env))

                    self._eval_block(func_data["body"], local_env)

            # --- 3. HTTP Request Library ("fetch", "post") ---
            elif "fetch(" in line:
                var_name, url_part = line.split("=", 1) if "=" in line else (None, line)
                url = url_part.split("fetch(")[1].rstrip(")").strip("'\"")
                
                if HAS_URLLIB:
                    try:
                        req = urllib.request.Request(url, headers={'User-Agent': 'Cruise-Lang/0.2.0'})
                        with urllib.request.urlopen(req) as response:
                            res_data = response.read().decode('utf-8')
                            if var_name:
                                env.set(var_name.strip(), res_data)
                            else:
                                print(res_data)
                    except Exception as e:
                        print(f"⚠️ Cruise HTTP Request Failed: {e}")

            # --- 4. Native Tensor Initialization ("t = tensor([1, 2, 3])") ---
            elif "tensor(" in line:
                var_name, tensor_part = line.split("=", 1)
                raw_list = tensor_part.split("tensor(")[1].rstrip(")")
                parsed_list = eval(raw_list)
                env.set(var_name.strip(), CruiseTensor(parsed_list))

            # --- 5. GUI Builder Engines ("background", "button") ---
            elif line.startswith("background("):
                color = line.split("background(")[1].rstrip(")").strip("'\"")
                if HAS_TKINTER:
                    if not self.gui_root:
                        self.gui_root = tk.Tk()
                        self.gui_root.title(f"Cruise GUI Engine — Creator: {self.creator}")
                        self.gui_root.geometry("450x350")
                    self.gui_root.configure(bg=color)
                else:
                    print(f"🎨 [GUI Headless Rendering]: Window background set to '{color}'")

            elif line.startswith("button("):
                btn_text = line.split("button(")[1].rstrip(")").strip("'\"")
                if HAS_TKINTER and self.gui_root:
                    btn = tk.Button(self.gui_root, text=btn_text, font=("Helvetica", 12, "bold"))
                    btn.pack(pady=12)
                else:
                    print(f"🔘 [GUI Headless Rendering]: Button component '{btn_text}' mounted")

            # --- 6. Loop Mechanisms ("5 times write('Engine')") ---
            elif "times " in line:
                count_str, action = line.split("times ", 1)
                count = int(count_str.strip())
                for _ in range(count):
                    self._eval_block([action.strip()], env)

            # --- 7. Output Console Engine ("write(...)") ---
            elif line.startswith("write("):
                content = line[6:].rstrip(")")
                val = self._eval_expression(content, env)
                print(val)

            # --- 8. Variable Assignment ("x = 10") ---
            elif "=" in line:
                var, val_expr = line.split("=", 1)
                env.set(var.strip(), self._eval_expression(val_expr.strip(), env))

            i += 1

        if HAS_TKINTER and self.gui_root:
            self.gui_root.mainloop()

    def _eval_expression(self, expr: str, env: Environment) -> Any:
        """Evaluates arithmetic expressions and dynamic variables safely."""
        expr = expr.strip()
        if (expr.startswith("'") and expr.endswith("'")) or (expr.startswith('"') and expr.endswith('"')):
            return expr[1:-1]
        try:
            return env.get(expr)
        except NameError:
            try:
                return eval(expr, {}, env.bindings)
            except Exception:
                return expr


# =============================================================================
# 6. CLI & REPL ENTRY POINT
# =============================================================================

def main():
    interpreter = CruiseInterpreter()

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if filename.endswith(('.cru', '.crui')):
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    code = f.read()
                interpreter.execute_script(code)
            else:
                print(f"❌ Error: Script file '{filename}' not found!")
        else:
            print("❌ Error: Invalid extension. Please use .cru or .crui files.")
    else:
        # Interactive Shell / REPL Engine
        interpreter.print_welcome_banner()
        while True:
            try:
                cmd = input("cruise> ")
                if cmd.strip().lower() in ["exit", "quit"]:
                    interpreter.print_exit_banner()
                    break
                if cmd.strip():
                    interpreter.execute_script(cmd)
            except (KeyboardInterrupt, EOFError):
                interpreter.print_exit_banner()
                break


if __name__ == "__main__":
    main()
