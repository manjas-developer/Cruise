<div align="center">

# 🚢 Cruise Programming Language (`cruise-lang`)

### **The AI-Ready, Human-Readable Programming Language Built for Speed & Simplicity**

![PyPI Version](https://img.shields.io/pypi/v/cruise-lang?color=0ea5e9)
![License](https://img.shields.io/badge/License-MIT-emerald.svg)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![GitHub Stars](https://img.shields.io/github/stars/manjas-developer/Cruise?style=social)

**Created & Developed with ❤️ by Manjas Anand**

</div>

---

> 🚢 **Cruise** is a lightweight, human-readable programming language designed for AI-ready scripting, tensor operations, machine learning, automation, and rapid development.

🌐 **Official Website & Documentation:**  
[manjas-developer.github.io/Cruise](https://manjas-developer.github.io/Cruise-Website/)

📦 **PyPI:**  
[cruise-lang on PyPI](https://pypi.org/project/cruise-lang/)

🐙 **GitHub:**  
[manjas-developer/Cruise](https://github.com/manjas-developer/Cruise)

---

## 📌 Table of Contents

- [🚢 Overview](#-overview)
- [⚡ Installation](#-installation)
- [🚀 Quick Start](#-quick-start)
- [💻 Interactive REPL](#-interactive-repl)
- [📄 Running Script Files](#-running-script-files)
- [📚 Language Syntax](#-language-syntax)
- [🖨️ Printing Output](#-printing-output)
- [📦 Variables](#-variables)
- [🧩 Functions](#-functions)
- [🔁 Loops](#-loops)
- [🔀 Conditions](#-conditions)
- [🧠 Tensor Support](#-tensor-support)
- [🌐 HTTP Requests](#-http-requests)
- [🖥️ GUI Components](#-gui-components)
- [✨ Features](#-features)
- [📂 Project Structure](#-project-structure)
- [🗺️ Roadmap](#-roadmap)
- [🤝 Contributing](#-contributing)
- [💖 Support Cruise](#-support-cruise)
  - [🇮🇳 Indian Support](#-indian-support)
  - [🌍 International Support](#-international-support)
- [📜 License](#-license)
- [👨‍💻 Creator](#-creator)

---

# 🚢 Overview

**Cruise** is a lightweight, modern, high-level programming language built with Python.

It focuses on making programming:

- 🚀 Simple and readable
- 🧠 Beginner-friendly
- ⚡ Fast to write
- 🤖 AI-ready
- 🔢 Tensor-friendly
- 🌐 Network-capable
- 🖥️ GUI-friendly
- 🔥 Easy to experiment with

Cruise is designed around the idea:

> **Write Less. Build More. Cruise Faster. 🚀**

---

# ⚡ Installation

Install or upgrade Cruise directly from PyPI:

    pip install --upgrade cruise-lang

---

# 🚀 Quick Start

## 💻 Interactive REPL

Start the Cruise interactive shell:

    cruise

Then run:

    write("Hello World!")

Output:

    Hello World!

---

# 📄 Running Script Files

Cruise supports both `.cru` and `.crui` files.

Example:

    main.cru

or:

    main.crui

Run a Cruise program using:

    cruise main.cru

---

# 📚 Language Syntax

## 🖨️ Printing Output

    write("Hello World!")

---

## 📦 Variables

    name = "Cruise"
    version = 2

    write(name)
    write(version)

---

## 🧩 Functions

    define greet(user):
        write("Welcome to Cruise Language, " + user + "!")
    end

    greet("Manjas")

---

## 🔁 Loops

    5 times write("Cruising Fast! 🚀")

---

## 🔀 Conditions

    if x > 10:
        write("Greater")
    end

---

# 🧠 Tensor Support

Cruise is designed with AI and numerical computing in mind.

Example:

    v1 = tensor([1.5, 2.5, 3.5])
    v2 = tensor([10.0, 20.0, 30.0])

    write(v1)
    write(v2)

---

# 🌐 HTTP Requests

Cruise can work with web APIs:

    data = fetch("https://api.github.com")
    write(data)

---

# 🖥️ GUI Components

Cruise also provides a simple syntax for GUI-oriented development:

    background("navy")

    button("Submit Form")
    button("Cancel")

---

# ✨ Features

| Feature | Status |
|---|---|
| 🚀 Human-readable syntax | ✅ |
| 🧠 Beginner-friendly design | ✅ |
| ⚡ Lightweight interpreter | ✅ |
| 💻 Interactive REPL | ✅ |
| 📁 `.cru` file support | ✅ |
| 📁 `.crui` file support | ✅ |
| 🌐 HTTP requests | ✅ |
| 📦 JSON support | ✅ |
| 🔢 Tensor objects | ✅ |
| 🤖 AI-ready scripting | 🚧 |
| 🖥️ GUI framework | 🚧 |
| 🧮 Tensor calculus | 🚧 |
| 📦 Package manager | 🚧 |
| 🧠 Advanced optimizer | 🚧 |

---

# 📂 Project Structure

    Cruise/
    │
    ├── cruise.py
    ├── lexer.py
    ├── parser.py
    ├── interpreter.py
    ├── runtime.py
    ├── stdlib.py
    ├── README.md
    └── LICENSE

---

# 🗺️ Roadmap

## ✅ v0.1.0

- Interactive REPL
- Variables
- Printing
- Basic Interpreter

---

## ✅ v0.2.0

- User-defined functions
- `.cru` support
- `.crui` support
- HTTP Requests
- Tensor Objects
- WebAssembly Support

---

## 🚧 v0.3.0

- Complete AST Parser
- Advanced Lexer
- Modules
- Package Manager
- GUI Framework
- Tensor Calculus
- Math Library
- Optimizer

---

# 🤝 Contributing

Contributions are welcome! ❤️

Whether you want to fix a bug, improve the interpreter, add a feature, improve documentation, or experiment with the language, you're welcome to contribute.

### 1️⃣ Fork the repository

Fork the Cruise repository on GitHub.

### 2️⃣ Create a new branch

    git checkout -b feature-name

### 3️⃣ Make your changes

Implement your feature or fix.

### 4️⃣ Commit your changes

    git add .
    git commit -m "Added new feature"

### 5️⃣ Push your branch

    git push origin feature-name

### 6️⃣ Open a Pull Request

Open a Pull Request on GitHub and describe your changes.

🎉 **Thank you for contributing to Cruise!**

---

# 💖 Support Cruise

If you enjoy Cruise, find it useful, or want to support its development, you can support the project below. 🚢❤️

Your support helps with:

- 🚀 Continued development
- 🧠 New language features
- 🤖 AI and tensor capabilities
- 🛠️ Development tools
- 📚 Documentation
- 🌐 Infrastructure
- 🔬 Future experiments

---

# 🇮🇳 Indian Support

If you're supporting from India, you can support Cruise here:

### ☕ Buy Me a Chai

[![Indian Support](https://img.shields.io/badge/🇮🇳%20Indian%20Support-Buy%20Me%20a%20Chai-orange?style=for-the-badge)](https://buymeachai.in/manjasanand08)

👉 **Support Here:**  
https://buymeachai.in/manjasanand08

---

# 🌍 International Support

If you're supporting from outside India, you can support Cruise here:

### 💜 Support via Throne

[![International Support](https://img.shields.io/badge/🌍%20International%20Support-Throne-purple?style=for-the-badge)](https://throne.com/manjas-developer/item/d83a6389-fc12-4d64-a4e1-cf4dc4d1dc45)

👉 **Support Here:**  
https://throne.com/manjas-developer/item/d83a6389-fc12-4d64-a4e1-cf4dc4d1dc45

---

<div align="center">

### ❤️ Thank You for Supporting Cruise!

**Every contribution helps keep Cruise moving forward. 🚢⚡**

</div>

---

# 📜 License

Cruise is licensed under the **MIT License**.

See the [`LICENSE`](LICENSE) file for complete license details.

---

# 👨‍💻 Creator

## Manjas Anand

**Developer & Creator of Cruise Programming Language**

### 📦 PyPI Package

    cruise-lang

[View Cruise on PyPI](https://pypi.org/project/cruise-lang/)

### 🐙 GitHub

    manjas-developer/Cruise

[View Cruise on GitHub](https://github.com/manjas-developer/Cruise)

### 🌐 Official Website & Documentation

    https://manjas-developer.github.io/Cruise-Website/

[Visit the Official Cruise Website](https://manjas-developer.github.io/Cruise-Website/)

### 📧 Contact

    manjasanand08@gmail.com

---

<div align="center">

# 🚢 Cruise Language

### **Write Less. Build More. Cruise Faster. 🚀**

Made with ❤️ in Python.

⭐ **If you like Cruise, consider giving the repository a star!**

</div>

---

<div align="center">

## 💖 Support Cruise

🇮🇳 **Indian Support:**  
[Buy Me a Chai](https://buymeachai.in/manjasanand08)

🌍 **International Support:**  
[Throne](https://throne.com/manjas-developer/item/d83a6389-fc12-4d64-a4e1-cf4dc4d1dc45)

</div>
