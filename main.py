import sys
import os
import math
import time
import json

# 1. HTTP Capabilities
try:
    import urllib.request
    import urllib.parse
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

# 2. GUI Driver Handling
HAS_TKINTER = False
try:
    if os.environ.get('DISPLAY') or os.name == 'nt' or sys.platform == 'darwin':
        import tkinter as tk
        HAS_TKINTER = True
except Exception:
    HAS_TKINTER = False


class CruiseTensor:
    """Lightweight Tensor Engine for AI/ML Operations."""
    def __init__(self, data):
        if isinstance(data, (int, float)):
            self.data = [float(data)]
            self.shape = (1,)
        elif isinstance(data, list):
            self.data = data
            self.shape = (len(data),)
        else:
            raise TypeError("Unsupported data type for CruiseTensor")

    def add(self, other):
        if isinstance(other, CruiseTensor):
            return CruiseTensor([a + b for a, b in zip(self.data, other.data)])
        return CruiseTensor([a + other for a in self.data])

    def multiply(self, other):
        if isinstance(other, CruiseTensor):
            return CruiseTensor([a * b for a, b in zip(self.data, other.data)])
        return CruiseTensor([a * other for a in self.data])

    def __repr__(self):
        return f"CruiseTensor(data={self.data}, shape={self.shape})"


class CruiseInterpreter:
    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.gui_root = None
        self.version = "0.3.0"
        self.creator = "Manjas Anand"

    def print_welcome_banner(self):
        """Displays startup personalized REPL banner."""
        print("=" * 65)
        print(f"  🚢 CRUISE LANGUAGE REPL v{self.version}")
        print(f"  👨‍💻 Designed & Developed by {self.creator}")
        print("  ⚡ Type 'exit' or 'quit' to close the shell")
        print("=" * 65)

    def print_exit_banner(self):
        """Displays exit personalized REPL banner."""
        print("\n" + "=" * 65)
        print(f"  👋 Thank you for using Cruise Language by {self.creator}!")
        print("  🚀 Keep building amazing AI models and apps. See you soon!")
        print("=" * 65)

    def execute_script(self, code_text):
        """Parse and run Cruise source scripts."""
        lines = [line.strip() for line in code_text.splitlines() if line.strip() and not line.strip().startswith("#")]
        self._run_lines(lines)

    def _run_lines(self, lines):
        i = 0
        while i < len(lines):
            line = lines[i]

            # --- 1. Function Definitions ("define func(a, b): ... end") ---
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

            # --- 2. Custom Function Call ---
            elif "(" in line and line.endswith(")") and not any(line.startswith(kw) for kw in ["write", "fetch", "post", "background", "button", "tensor"]):
                func_name, args_part = line.rstrip(")").split("(", 1)
                func_name = func_name.strip()

                if func_name in self.functions:
                    raw_args = [a.strip() for a in args_part.split(",") if a.strip()]
                    func_data = self.functions[func_name]

                    local_env = {}
                    for param, val in zip(func_data["args"], raw_args):
                        local_env[param] = eval(val, {}, self.variables)

                    saved_vars = self.variables.copy()
                    self.variables.update(local_env)
                    self._run_lines(func_data["body"])
                    self.variables = saved_vars

            # --- 3. HTTP Request Support ---
            elif "fetch(" in line:
                var_name, url_part = line.split("=", 1) if "=" in line else (None, line)
                url = url_part.split("fetch(")[1].rstrip(")").strip("'\"")
                
                if HAS_URLLIB:
                    try:
                        req = urllib.request.urlopen(url)
                        res_data = req.read().decode('utf-8')
                        if var_name:
                            self.variables[var_name.strip()] = res_data
                        else:
                            print(res_data)
                    except Exception as e:
                        print(f"⚠️ Cruise HTTP Error: {e}")

            # --- 4. Tensor Creation ("t = tensor([1, 2, 3])") ---
            elif "tensor(" in line:
                var_name, tensor_part = line.split("=", 1)
                raw_list = tensor_part.split("tensor(")[1].rstrip(")")
                parsed_list = eval(raw_list)
                self.variables[var_name.strip()] = CruiseTensor(parsed_list)

            # --- 5. GUI Builder ---
            elif line.startswith("background("):
                color = line.split("background(")[1].rstrip(")").strip("'\"")
                if HAS_TKINTER:
                    if not self.gui_root:
                        self.gui_root = tk.Tk()
                        self.gui_root.title(f"Cruise GUI App — Developed by {self.creator}")
                        self.gui_root.geometry("400x300")
                    self.gui_root.configure(bg=color)
                else:
                    print(f"🎨 [GUI Headless Mode]: Background set to '{color}'")

            elif line.startswith("button("):
                btn_text = line.split("button(")[1].rstrip(")").strip("'\"")
                if HAS_TKINTER and self.gui_root:
                    btn = tk.Button(self.gui_root, text=btn_text)
                    btn.pack(pady=10)
                else:
                    print(f"🔘 [GUI Headless Mode]: Button '{btn_text}' rendered")

            # --- 6. Loop Mechanics ("5 times write('Cruise')") ---
            elif "times " in line:
                count_str, action = line.split("times ", 1)
                count = int(count_str.strip())
                for _ in range(count):
                    self._run_lines([action.strip()])

            # --- 7. Print Statements ("write(...)") ---
            elif line.startswith("write("):
                content = line[6:].rstrip(")")
                if content in self.variables:
                    print(self.variables[content])
                else:
                    try:
                        print(eval(content, {}, self.variables))
                    except Exception:
                        print(content.strip("'\""))

            # --- 8. Variable Assignment ---
            elif "=" in line:
                var, val = line.split("=", 1)
                self.variables[var.strip()] = eval(val.strip(), {}, self.variables)

            i += 1

        if HAS_TKINTER and self.gui_root:
            self.gui_root.mainloop()


# --- CLI ENTRY POINT & REPL RUNNER ---
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
                print(f"❌ Error: File '{filename}' not found!")
        else:
            print("❌ Error: Invalid file extension. Please use .cru or .crui")
    else:
        # Interactive REPL Session
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
