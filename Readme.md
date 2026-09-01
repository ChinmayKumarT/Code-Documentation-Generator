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

## Deployment

The app is a plain Flask service with no database and no external API calls.
A built image is ~150 MB and it idles in well under 256 MB of RAM, so it fits
any small instance (Render/Railway/Fly free or hobby tier).

### Run it locally

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows;  source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
python app.py                  # http://127.0.0.1:5000
```

### Deploy with Docker

```bash
docker build -t code-doc-generator .
docker run -p 8000:8000 code-doc-generator
```

### Deploy to Render / Railway

Push the repo to GitHub and create a new Web Service pointing at it. Both
hosts detect the `Dockerfile` automatically; if you would rather not use
Docker, they will also read the `Procfile`. Set the build command to
`pip install -r requirements.txt` in that case. No environment variables are
required.

### Things to know before going live

- **Never set `FLASK_DEBUG=1` on a public host.** It enables the Werkzeug
  debugger, which is a remote Python console for anyone who finds the URL.
  `app.py` defaults it off; production runs under gunicorn, which ignores
  that block entirely.
- **Run exactly one worker** (`-w 1`, as configured). Reports are written to
  `temp/<uuid>/` by the worker that generated them and fetched by a later
  `/download` request. Additional workers or instances would 404 on reports
  they did not create. Scaling past one process requires shared storage or
  returning the files inline.
- Generated reports are swept after one hour. Override with
  `SESSION_TTL_SECONDS`.
- Uploads are parsed, never executed. Keep it that way: the unused
  `extract_sample_io()` in `analyzer/report_generator.py` calls `exec()` on
  uploaded source and would be a remote code execution hole if re-enabled.

### AI summarizer

`analyzer/summarizer.py` wraps a CodeT5-small checkpoint. It is **not used**.
It was passed the file *path* rather than the file *contents*, so it summarised
UUIDs; and even given real source this checkpoint emits code fragments rather
than English. Every summary was therefore produced by `build_paragraph()`,
which reads the parsed structure directly. Removing the call cut the image from
~1 GB to ~150 MB and a request from ~30 s to ~0.2 s with identical output.

To revisit it: reinstate `torch` and `transformers` in `requirements.txt`, pass
the source text (not the path) to `summarize_code()`, load the model once at
import rather than per request, and relax `is_bad_summary()` — it currently
rejects any text containing a programming keyword.

## Workflow Diagram

```text
+------------------+        +--------------------+        +--------------------+
| Python Source    |  --->  | Documentation      |  --->  | Output: JSON/MD    |
| Code Files       |        | Generator Script   |        | Summary File       |
+------------------+        +--------------------+        +--------------------+
```

## 