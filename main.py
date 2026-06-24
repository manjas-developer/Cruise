import re
import sys
import os
import tkinter as tk
import torch  # Powered by PyTorch for Tensors, Autograd, and GPU access
from sklearn.linear_model import LinearRegression
import numpy as np

# --- 1. Global Setup for the Cruise Language ---
variables = {}
memory_log = []  
ml_models = {}   
root = None      # Holds the Tkinter window object if UI features are used

# Pre-train a simple background ML model for "house_prices"
X_train = np.array([[1], [2], [3], [4]])
y_train = np.array([100, 200, 300, 400])
house_model = LinearRegression()
house_model.fit(X_train, y_train)
ml_models["house_prices"] = house_model


# --- 2. The Core Cruise Interpreter Engine ---
def run_line(line):
    global root
    line = line.strip()
    
    # Ignore empty lines or comments
    if not line or line.startswith("#"):
        return

    # A. Audio Alert: beep()
    if line == "beep()":
        print("\a", end="", flush=True) 
        return

    # B. Window Background Color: background("color")
    if line.startswith("background"):
        match = re.match(r'background\(\s*"(.*?)"\s*\)', line)
        if match:
            color = match.group(1)
            if root is None:
                root = tk.Tk()
                root.title("Cruise App")
                root.geometry("400x400")
            root.configure(bg=color)
        return

    # C. Automation Loops: [number] times [command]
    if " times " in line:
        match = re.match(r"(\d+)\s+times\s+(.+)", line)
        if match:
            iterations = int(match.group(1))
            command_to_run = match.group(2).strip()
            for _ in range(iterations):
                run_line(command_to_run)
        return

    # D. Long-term Memory: remember(variable)
    if line.startswith("remember"):
        match = re.search(r'remember\(\s*(\w+)\s*\)', line)
        if match:
            var_name = match.group(1)
            if var_name in variables:
                memory_log.append(variables[var_name])
                print(f"[Cruise Memory]: Logged value of '{var_name}' -> ({variables[var_name]})")
            else:
                print(f"Cruise Error: Cannot remember '{var_name}', variable does not exist.")
        return

    # E. File Logging Forms: log("path", variable)
    if line.startswith("log"):
        match = re.match(r'log\(\s*"(.*?)"\s*,\s*(.*?)\s*\)', line)
        if match:
            file_path = match.group(1)
            var_name = match.group(2).strip()
            
            data_to_save = str(variables[var_name]) if var_name in variables else var_name.strip('"')
            try:
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(data_to_save + "\n")
                print(f"[Cruise File Logged]: Saved '{data_to_save}' to '{file_path}'")
            except Exception as e:
                print(f"Cruise File Error: Could not write to file. {e}")
        return

    # F. UI Interactive Buttons: button("Label", action, "optional_color")
    if line.startswith("button"):
        if root is None:
            root = tk.Tk()
            root.title("Cruise App")
            root.geometry("400x400")

        match = re.match(r'button\(\s*"(.*?)"\s*,\s*([^,)]+)(?:\s*,\s*"(.*?)")?\s*\)', line)
        if match:
            button_text = match.group(1)
            action_command = match.group(2).strip()
            btn_color = match.group(3) if match.group(3) else "lightgray"

            def on_click():
                run_line(action_command)

            tk_button = tk.Button(root, text=button_text, command=on_click, bg=btn_color, activebackground=btn_color)
            tk_button.pack(pady=10)
        return

    # G. Tensor Core Array Support: let [name] be array([...])
    if line.startswith("let ") and "array(" in line:
        match = re.match(r"let\s+(\w+)\s+be\s+array\((.+)\)", line)
        if match:
            var_name = match.group(1)
            array_data = eval(match.group(2))
            variables[var_name] = torch.tensor(array_data, dtype=torch.float32, requires_grad=True)
            print(f"[Cruise Array]: Created tensor '{var_name}' with Autograd tracking.")
        return

    # H. GPU Access Accelerator Binding: let [name] be moved to gpu
    if "moved to gpu" in line:
        match = re.match(r"let\s+(\w+)\s+be\s+moved to gpu", line)
        if match:
            var_name = match.group(1)
            if var_name in variables:
                if torch.cuda.is_available():
                    variables[var_name] = variables[var_name].to("cuda")
                    print(f"[Cruise GPU]: Accelerated '{var_name}' by moving to GPU (CUDA).")
                else:
                    print("[Cruise GPU Warning]: GPU hardware not found. Cruising smoothly on CPU instead.")
            else:
                print(f"Cruise Error: Variable '{var_name}' not found.")
        return

    # I. Autograd Gradient Solver: compute_gradients([tensor])
    if line.startswith("compute_gradients"):
        match = re.match(r"compute_gradients\((.+)\)", line)
        if match:
            var_name = match.group(1).strip()
            if var_name in variables:
                variables[var_name].backward(torch.ones_like(variables[var_name]))
                print(f"[Cruise Autograd]: Backward pass completed for '{var_name}'. Derivatives calculated!")
            else:
                print(f"Cruise Error: Variable '{var_name}' not found.")
        return

    # J. Display Mathematical Gradients: write_gradient([tensor])
    if line.startswith("write_gradient"):
        match = re.match(r"write_gradient\((.+)\)", line)
        if match:
            var_name = match.group(1).strip()
            if var_name in variables and variables[var_name].grad is not None:
                print(f"Gradient of {var_name}: {variables[var_name].grad}")
            else:
                print(f"Cruise Error: No gradients discovered for '{var_name}'. Did you trigger compute_gradients()?")
        return

    # K. Core Variable Engine, Basic Math, & ML Predictions
    if line.startswith("let "):
        match = re.match(r"let\s+(\w+)\s+be\s+(.+)", line)
        if match:
            var_name = match.group(1)
            var_value_raw = match.group(2).strip()
            
            # Interactive Console Inputs
            if var_value_raw.startswith("ask"):
                prompt_match = re.search(r'ask\(\s*"(.*?)"\s*\)', var_value_raw)
                if prompt_match:
                    user_input = input(prompt_match.group(1))
                    try:
                        variables[var_name] = float(user_input) if '.' in user_input else int(user_input)
                    except ValueError:
                        variables[var_name] = user_input
                return

            # Native Machine Learning Predictor
            if var_value_raw.startswith("predict"):
                ml_match = re.search(r'predict\(\s*"(.*?)"\s*,\s*(.*?)\s*\)', var_value_raw)
                if ml_match:
                    model_name = ml_match.group(1)
                    input_val_raw = ml_match.group(2)
                    input_val = float(variables[input_val_raw]) if input_val_raw in variables else float(input_val_raw)
                    
                    if model_name in ml_models:
                        prediction = ml_models[model_name].predict([[input_val]])[0]
                        variables[var_name] = round(prediction, 2)
                    else:
                        print(f"Cruise ML Error: Model '{model_name}' unrecognized.")
                return
            
            # Normal assignments and matrix/tensor math calculations
            try:
                local_env = {**globals(), **variables}
                variables[var_name] = eval(var_value_raw, local_env)
            except:
                if var_value_raw.startswith('"') and var_value_raw.endswith('"'):
                    variables[var_name] = var_value_raw.strip('"')
                else:
                    print(f"Cruise Error: Could not assign value to '{var_name}'")
        return

    # L. Logical Conditions: if [condition] then [command]
    if line.startswith("if "):
        match = re.match(r"if\s+(.+)\s+then\s+(.+)", line)
        if match:
            condition_raw = match.group(1).strip()
            action_command = match.group(2).strip()
            
            for name, val in variables.items():
                if isinstance(val, (int, float)):
                    condition_raw = re.sub(rf'\b{name}\b', str(val), condition_raw)
                elif isinstance(val, str):
                    condition_raw = re.sub(rf'\b{name}\b', f'"{val}"', condition_raw)
            try:
                if eval(condition_raw):
                    run_line(action_command)
            except:
                print("Cruise Syntax Error: Conditional expression evaluation failed.")
        return

    # M. Native Standard Output: write(...)
    if line.startswith("write"):
        content = re.search(r'\((.*?)\)', line).group(1).strip()
        if content in variables:
            print(variables[content])
        elif content == "memory":
            print(f"Cruise Memory Timeline: {memory_log}")
        else:
            try:
                local_env = {**globals(), **variables}
                print(eval(content, local_env))
            except:
                print("Cruise Syntax Error inside write()")
        return

    print(f"Cruise Syntax Error: Command '{line}' unrecognized.")


def run_program(program_code):
    lines = program_code.split('\n')
    for line in lines:
        run_line(line)
    if root is not None:
        print("\n[Cruise UI Window Running]: Visual app activated.")
        root.mainloop()


# --- 3. Terminal Execution Manager ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            with open(filename, "r", encoding="utf-8") as file:
                run_program(file.read())
        except FileNotFoundError:
            print(f"Cruise File System Error: '{filename}' not found.")
    else:
        print("--- Running Cruise AI/Deep-Learning Test Script ---")
        demo_script = """
        let x be array([1.0, 3.0, 5.0])
        let y be x * x + 10
        let y be moved to gpu
        write("Matrix processing values (x^2 + 10):")
        write(y)
        compute_gradients(y)
        write("Calculated calculus weights via Cruise Autograd:")
        write_gradient(x)
        """
        run_program(demo_script)
