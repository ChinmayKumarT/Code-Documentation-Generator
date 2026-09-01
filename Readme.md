# Code Documentation System

A Python-based system to automatically generate documentation for Python code.  
It extracts function names, their time complexity, examples, and produces a structured summary in JSON or Markdown format.

---

## Features

- Parses Python source files and identifies functions.
- Extracts function details including:
  - Name
  - Parameters
  - Time complexity
- Generates structured documentation in JSON or Markdown format.
- Easy to extend for more analysis (e.g., class methods, modules).

---

## Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

2. Create a Python virtual environment:

```bash
python3.12 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Place your Python files inside the examples/ folder.
2. Run the documentation generator script: 
```bash
python main.py examples/filename
```
3. Output:
- summary.json → JSON structured documentation.
- summary.md → Markdown formatted documentation.

## Example Output

JSON Example:

```json
{
    "summary": {
        "paragraph": "probabilities",
        "points": [
            "Function: factorial(n) → Complexity: O(n), Example: factorial(9) → 362880",
            "Function: square(self, x) → Complexity: O(1), Example: square(5) → 25"
        ]
    }
}
```

Markdown Example:

```markdown
### Function: factorial(n)
- Complexity: O(n)
- Example: factorial(9) → 362880

### Function: square(self, x)
- Complexity: O(1)
- Example: square(5) → 25

```

## Workflow Diagram

```text
+------------------+        +--------------------+        +--------------------+
| Python Source    |  --->  | Documentation      |  --->  | Output: JSON/MD    |
| Code Files       |        | Generator Script   |        | Summary File       |
+------------------+        +--------------------+        +--------------------+
```

## 