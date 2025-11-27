Project: Mini C++ Compiler (Python prototype)

This toy project implements a simplified compiler front-end for a subset of C++:
- Lexical analysis (tokenizer)
- Recursive-descent parsing to an AST
- A basic semantic analyzer (scope checks, undeclared identifiers)

Files:
- `src/lexer.py` — tokenizer
- `src/ast.py` — AST node classes
- `src/parser.py` — parser producing AST
- `src/semantic.py` — semantic checks
- `run.py` — simple CLI runner
- `examples/test1.cpp` — sample input

Run:
Open PowerShell and run:

```powershell
python run.py .\examples\test1.cpp
```

Run all example tests:

```powershell
python run_tests.py
```

Notes:
- This is a minimal, educational prototype. It intentionally omits many C++ features.
- You can extend `src/parser.py` and `src/semantic.py` to add more constructs and checks.
