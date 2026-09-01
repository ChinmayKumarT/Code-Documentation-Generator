import json
import re
import ast
import os
import random
from analyzer.code_parser import parse_code
from analyzer.complexity import analyze_complexity
# NOTE: analyzer.summarizer (CodeT5) is intentionally not imported here — it
# pulls in torch/transformers (~600MB) and its output was always discarded.

# ReportLab for PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    ListFlowable, ListItem, Table, TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


# -------- Helpers -------- #

def build_paragraph(parsed_info: dict) -> str:
    """Generate a natural language description of the code structure."""
    parts = []
    
    # Handle classes first
    if "classes" in parsed_info and parsed_info["classes"]:
        class_descs = []
        for cls in parsed_info["classes"][:3]:  # Limit to first 3 classes for brevity
            if not isinstance(cls, dict):
                continue
                
            class_name = cls.get("name", "")
            methods = []
            
            # Get methods for this class, excluding dunder methods
            if "methods" in cls and cls["methods"]:
                methods = [
                    m["name"] if isinstance(m, dict) else str(m) 
                    for m in cls["methods"]
                    if not (isinstance(m, dict) and m.get("name", "").startswith('__'))
                ]
            
            # Format class description
            if methods:
                method_list = ", ".join(methods[:3])
                more = f" and {len(methods) - 3} more" if len(methods) > 3 else ""
                class_descs.append(f"{class_name} with methods like {method_list}{more}")
            else:
                class_descs.append(class_name)
        
        if class_descs:
            parts.append(f"defines classes including {', '.join(class_descs)}")
    
    # Handle top-level functions (non-class methods)
    if "functions" in parsed_info and parsed_info["functions"]:
        funcs = [
            f["name"] if isinstance(f, dict) else str(f) 
            for f in parsed_info["functions"]
            if not (isinstance(f, dict) and f.get("name", "").startswith('__'))
        ]
        if funcs:
            func_list = ", ".join(funcs[:3])
            more = f" and {len(funcs) - 3} more" if len(funcs) > 3 else ""
            parts.append(f"defines functions including {func_list}{more}")
    
    # Handle top-level variables if any
    if "variables" in parsed_info and parsed_info["variables"]:
        vars_list = [v["name"] if isinstance(v, dict) else str(v) 
                    for v in parsed_info["variables"][:3]]
        if vars_list:
            more = " and more" if len(parsed_info["variables"]) > 3 else ""
            parts.append(f"declares variables including {', '.join(vars_list)}{more}")
    
    if not parts:
        return "This code contains basic definitions and logic."
    
    # Join the parts with appropriate punctuation
    if len(parts) == 1:
        return parts[0].capitalize() + "."
    return ", ".join(parts[:-1]) + ", and " + parts[-1] + "."

def _build_method_map(parsed_info: dict) -> dict:
    """Build a mapping of method names to their containing class/struct."""
    method_map = {}
    
    # Handle methods in classes/structs
    for container_type in ["classes", "structs"]:
        if container_type in parsed_info:
            for container in parsed_info[container_type]:
                if not isinstance(container, dict):
                    continue
                container_name = container.get("name", "")
                if "methods" in container:
                    for method in container["methods"]:
                        if isinstance(method, dict):
                            method_map[method["name"]] = container_name
                        else:
                            method_map[method] = container_name
    
    # Handle top-level functions/methods
    for func_key in ["functions", "methods"]:
        if func_key in parsed_info:
            for func in parsed_info[func_key]:
                if isinstance(func, dict):
                    method_map[func["name"]] = ""
                else:
                    method_map[func] = ""
    
    return method_map

def format_summary(summary: str, parsed_info: dict, complexity_info: dict, samples: dict) -> dict:
    """Format the summary section of the report."""
    # For Java files, we'll build a custom summary since the AI-generated one might be poor
    if any(key in parsed_info for key in ["methods", "fields"]):  # Likely Java or similar
        paragraph_text = ""
        
        # Add class information
        if "classes" in parsed_info and parsed_info["classes"]:
            class_names = [c.get("name", "") for c in parsed_info["classes"] if isinstance(c, dict)]
            if class_names:
                paragraph_text += f"This file contains the following classes: {', '.join(class_names)}. "
        
        # Add method information
        if "methods" in parsed_info and parsed_info["methods"]:
            method_names = [m.get("name", "") for m in parsed_info["methods"] if isinstance(m, dict)]
            if method_names:
                paragraph_text += f"It includes methods such as: {', '.join(method_names[:5])}"
                if len(method_names) > 5:
                    paragraph_text += f" and {len(method_names) - 5} more."
                else:
                    paragraph_text += "."
    else:
        # For Python and other languages, use the existing logic
        if is_bad_summary(summary, parsed_info):
            paragraph_text = build_paragraph(parsed_info)
        else:
            paragraph_text = summary.strip()

    method_map = _build_method_map(parsed_info)
    points = []

    # Process methods (Java) or functions (Python)
    func_key = "methods" if "methods" in parsed_info else "functions"
    if func_key in parsed_info:
        for func in parsed_info[func_key]:
            if not isinstance(func, dict):
                continue
                
            name = func.get("name", "")
            args = func.get("args", [])
            if not isinstance(args, list):
                args = []
            
            # Skip constructors in Java (they have the same name as the class)
            if "classes" in parsed_info and any(name == cls.get("name") for cls in parsed_info["classes"] if isinstance(cls, dict)):
                continue
            
            # Handle method resolution
            display_name = name
            if name in method_map and method_map[name]:
                display_name = f"{method_map[name]}.{name}"
            
            # Get complexity info
            comp_val = next(
                (c["complexity"] for c in complexity_info.get("cyclomatic_complexity", []) 
                 if c["name"] == name),
                None
            )
            big_o = map_complexity_to_big_o(comp_val)
            
            # Format the point
            arg_str = ", ".join(args) if args else ""
            point = f"{display_name}({arg_str})"
            if big_o != "Unknown":
                point += f" → Complexity: {big_o}"
            
            points.append(point)

    # Add classes/structs
    for container_type, display_name in [("classes", "Class"), ("structs", "Struct")]:
        if container_type in parsed_info:
            for item in parsed_info[container_type]:
                if not isinstance(item, dict):
                    continue
                    
                name = item.get("name", "")
                methods = item.get("methods", [])
                if methods:
                    method_list = ", ".join([m["name"] if isinstance(m, dict) else str(m) for m in methods])
                    points.append(f"{display_name}: {name} → methods: {method_list}")
                else:
                    points.append(f"{display_name}: {name}")

    # Add variables/fields
    for var_key, display_name in [("variables", "Variable"), ("fields", "Field")]:
        if var_key in parsed_info:
            for var in parsed_info[var_key]:
                if isinstance(var, dict):
                    points.append(f"{display_name}: {var.get('name', '')}")
                elif isinstance(var, str):
                    points.append(f"{display_name}: {var}")

    return {
        "paragraph": paragraph_text,
        "points": points
    }

def format_parsed_info(parsed_info: dict, for_pdf: bool = False) -> list:
    """Format parsed information into a list of strings for display."""
    lines = []
    b0, b1 = ("<b>", "</b>") if for_pdf else ("**", "**")
    
    def add_section(title, items, item_formatter):
        if not items:
            return
        lines.append(f"{b0}{title}{b1}")
        for item in items:
            lines.append(item_formatter(item))
        lines.append("")
    
    # Format class/struct information
    for type_key, display_name in [("classes", "Classes"), ("structs", "Structures")]:
        if type_key in parsed_info and parsed_info[type_key]:
            items = []
            for item in parsed_info[type_key]:
                if not isinstance(item, dict):
                    items.append(f"- {item}")
                    continue
                    
                name = item.get("name", "")
                methods = item.get("methods", [])
                if methods:
                    method_list = ", ".join([m["name"] if isinstance(m, dict) else str(m) for m in methods])
                    items.append(f"- {name} → methods: {method_list}")
                else:
                    items.append(f"- {name}")
            
            if items:
                lines.append(f"{b0}{display_name}{b1}")
                lines.extend(items)
                lines.append("")
    
    # Format functions/methods
    for func_key, display_name in [("functions", "Functions"), ("methods", "Methods")]:
        if func_key in parsed_info and parsed_info[func_key]:
            items = []
            for func in parsed_info[func_key]:
                if isinstance(func, dict):
                    name = func.get("name", "")
                    args = ", ".join([a for a in func.get("args", []) if a not in ("self", "cls")])
                    items.append(f"- {name}({args})")
                else:
                    items.append(f"- {func}()")
            
            if items:
                lines.append(f"{b0}{display_name}{b1}")
                lines.extend(items)
                lines.append("")
    
    # Format variables/fields
    for var_key, display_name in [("variables", "Variables"), ("fields", "Fields")]:
        if var_key in parsed_info and parsed_info[var_key]:
            items = []
            for var in parsed_info[var_key]:
                if isinstance(var, dict):
                    items.append(f"- {var.get('name', '')}")
                else:
                    items.append(f"- {var}")
            
            if items:
                lines.append(f"{b0}{display_name}{b1}")
                lines.extend(items)
                lines.append("")
    
    return lines

def map_complexity_to_big_o(value: int) -> str:
    if value is None:
        return "Unknown"
    if value <= 1:
        return "O(1)"
    elif value <= 3:
        return "O(n)"
    else:
        return "O(n²)"

def _generate_int() -> int:
    return random.randint(1, 10)

def extract_sample_io(filepath: str) -> dict:
    """
    Executes the module in a shared env so recursion works,
    then tries to call top-level functions and instance methods
    with a simple int argument when possible.
    """
    samples = {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        env = {}
        exec(code, env, env)  # NOTE: executes user code

        tree = ast.parse(code)

        # Top-level functions
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                name = node.name
                fn_obj = env.get(name)
                if callable(fn_obj):
                    # Try one-arg int functions; otherwise skip gracefully
                    n_args = len(node.args.args)
                    try:
                        if n_args == 1:
                            x = _generate_int()
                            out = fn_obj(x)
                            samples[name] = {"input": str(x), "output": str(out)}
                        else:
                            # For multi-arg, try all ints = 1
                            xs = [1] * n_args
                            out = fn_obj(*xs)
                            samples[name] = {
                                "input": ", ".join(map(str, xs)),
                                "output": str(out)
                            }
                    except Exception as e:
                        samples[name] = {"input": "-", "output": f"Error: {e}"}

            # Classes & instance methods
            elif isinstance(node, ast.ClassDef):
                cls_name = node.name
                cls_obj = env.get(cls_name)
                if cls_obj is None:
                    continue
                # Try to instantiate without args
                try:
                    inst = cls_obj()
                except Exception:
                    inst = None
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name != "__init__":
                        meth_name = item.name
                        sample_key = f"{cls_name}.{meth_name}"
                        if inst is None:
                            samples[sample_key] = {"input": "-", "output": "Instantiation failed"}
                            continue
                        meth = getattr(inst, meth_name, None)
                        if not callable(meth):
                            continue
                        # infer arg count excluding 'self'
                        n_args = max(0, len(item.args.args) - 1)
                        try:
                            if n_args == 0:
                                out = meth()
                                samples[sample_key] = {"input": "-", "output": str(out)}
                            elif n_args == 1:
                                x = _generate_int()
                                out = meth(x)
                                samples[sample_key] = {"input": str(x), "output": str(out)}
                            else:
                                xs = [1] * n_args
                                out = meth(*xs)
                                samples[sample_key] = {
                                    "input": ", ".join(map(str, xs)),
                                    "output": str(out)
                                }
                        except Exception as e:
                            samples[sample_key] = {"input": "-", "output": f"Error: {e}"}

    except Exception as e:
        samples["error"] = str(e)

    return samples

def is_bad_summary(text: str, parsed_info: dict) -> bool:
    if not text or not isinstance(text, str):
        return True
        
    t = text.strip()
    
    # Check for empty or very short text
    if len(t) < 10:  
        return True
        
    # Check for one-word or digits/symbols only
    if len(t.split()) < 3:
        return True
        
    # Check for code-like patterns or malformed text
    if re.search(r'[\[\]{}()=+*&^%$#@!~`\|\\/<>?]', t) and len(t.split()) < 5:
        return True
        
    # Check for common error patterns
    error_patterns = [
        r'\b(?:error|exception|failed|invalid|undefined)\b',
        r'[.:]\s*[A-Z]',  
        r'\b(?:function|class|def|var|let|const)\s+[a-zA-Z0-9_]+\s*[=({]',  
        r'\b(?:return|if|else|for|while|switch|case|break|continue|try|catch|throw|new|delete|typeof|instanceof|void|in|of|yield|await|async|import|export|from|as|default|extends|implements|interface|package|private|protected|public|static|with|debugger|enum|eval|arguments|this|super|true|false|null|undefined|NaN|Infinity|Date|Math|JSON|Array|Object|Function|String|Number|Boolean|RegExp|Error|EvalError|RangeError|ReferenceError|SyntaxError|TypeError|URIError|ArrayBuffer|DataView|Float32Array|Float64Array|Int8Array|Int16Array|Int32Array|Uint8Array|Uint8ClampedArray|Uint16Array|Uint32Array|Map|Set|WeakMap|WeakSet|Promise|Generator|GeneratorFunction|AsyncFunction|Proxy|Reflect|Symbol|Intl|WebAssembly|Atomics|SharedArrayBuffer)\b',
    ]
    
    for pattern in error_patterns:
        if re.search(pattern, t, re.IGNORECASE):
            return True
    
    # Check for incomplete sentences or code fragments
    if re.search(r'[.:;!?]\s*[a-z]', t):  
        return True
        
    # Check if the text contains any code-like patterns without proper context
    code_like = re.search(r'\b(?:def|class|function|var|let|const|import|from|export|return|if|else|for|while|switch|case|break|continue|try|catch|finally|throw|new|delete|typeof|instanceof|void|in|of|yield|await|async|as|default|extends|implements|interface|package|private|protected|public|static|with|debugger|enum|eval|arguments|this|super|true|false|null|undefined|NaN|Infinity)\b', t)
    if code_like and len(t.split()) < 10:  
        return True
    
    # Must mention at least one function/class name if they exist
    names = set()
    for fn in parsed_info.get("functions", []):
        if isinstance(fn, dict) and "name" in fn:
            names.add(fn["name"].lower())
    for cls in parsed_info.get("classes", []):
        if isinstance(cls, dict) and "name" in cls:
            names.add(cls["name"].lower())
    
    if names and not any(re.search(r'\b' + re.escape(n) + r'\b', t.lower()) for n in names):
        return True
        
    return False

def dict_to_table(data: list, title: str):
    if not data:
        return Paragraph(f"<i>No {title}</i>", getSampleStyleSheet()["Normal"])
    headers = list(data[0].keys())
    rows = [headers]
    for item in data:
        rows.append([str(item.get(h, "")) for h in headers])
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    return table

# -------- PDF Generator -------- #

def save_pdf(report: dict, pdf_path: str = "outputs/report.pdf") -> None:
    """
    Save the report as a PDF file.
    
    Args:
        report: The report dictionary
        pdf_path: Path to save the PDF file
    """
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Add title
    story.append(Paragraph(f"<b>Code Documentation Report</b>: {report['file']}", styles["Title"]))
    story.append(Spacer(1, 16))

    # Add summary
    story.append(Paragraph("<b>Summary</b>", styles["Heading2"]))
    story.append(Paragraph(report["summary"]["paragraph"], styles["Normal"]))
    story.append(Spacer(1, 12))

    # Add details if available
    if report["summary"].get("points"):
        story.append(Paragraph("<b>Details</b>", styles["Heading2"]))
        bullet_items = [ListItem(Paragraph(p, styles["Normal"])) for p in report["summary"]["points"]]
        story.append(ListFlowable(bullet_items, bulletType="bullet", leftIndent=20))
        story.append(Spacer(1, 12))

    # Add sample I/O section if available
    samples = report.get("samples", {})
    if isinstance(samples, dict) and samples:
        story.append(Paragraph("<b>Sample Input/Output</b>", styles["Heading2"]))
        
        if "error" in samples:
            story.append(Paragraph(f"<i>{samples['error']}</i>", styles["Italic"]))
        elif "info" in samples:
            story.append(Paragraph(samples["info"], styles["Normal"]))
        else:
            # Only show the table if we have proper I/O samples
            rows = [["Function/Method", "Input", "Output"]]
            for fn, io in samples.items():
                if isinstance(io, dict):
                    rows.append([
                        fn, 
                        str(io.get("input", "-")), 
                        str(io.get("output", "-"))
                    ])
            
            if len(rows) > 1:  # If we have data rows
                table = Table(rows, hAlign="LEFT", colWidths=[doc.width/3]*3)
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.lightgrey),
                    ("WORDWRAP", (0, 0), (-1, -1)),
                ]))
                story.append(table)
            else:
                story.append(Paragraph("No sample I/O data available.", styles["Italic"]))
            
        story.append(Spacer(1, 12))

    # Add parsed information
    story.append(Paragraph("<b>Code Structure</b>", styles["Heading2"]))
    for line in format_parsed_info(report["parsed_info"], for_pdf=True):
        story.append(Paragraph(line, styles["Normal"]))
    story.append(Spacer(1, 12))

    # Add complexity information
    story.append(Paragraph("<b>Complexity Analysis</b>", styles["Heading2"]))
    
    # Cyclomatic Complexity
    complexity_data = report["complexity_info"].get("cyclomatic_complexity", [])
    if complexity_data:
        story.append(Paragraph("Cyclomatic Complexity:", styles["Heading3"]))
        rows = [["Name", "Complexity (Big-O)"]]
        for item in complexity_data:
            if isinstance(item, dict):
                rows.append([
                    item.get("name", ""),
                    map_complexity_to_big_o(item.get("complexity"))
                ])
        
        if len(rows) > 1:  # If we have data rows
            table = Table(rows, hAlign="LEFT", colWidths=[doc.width*2/3, doc.width/3])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.lightgrey),
            ]))
            story.append(table)
        story.append(Spacer(1, 12))
    
    # Halstead metrics if available
    halstead = report["complexity_info"].get("halstead_metrics")
    if isinstance(halstead, dict):
        story.append(Paragraph("<b>Halstead Metrics</b>", styles["Heading3"]))
        
        # Convert metrics to a displayable format
        metrics = []
        for key, value in halstead.items():
            if key == "note":
                continue
            if isinstance(value, float):
                metrics.append((key, f"{value:.2f}"))
            else:
                metrics.append((key, str(value)))
        
        if metrics:
            # Create a table with metrics
            table_data = []
            for i in range(0, len(metrics), 2):
                row = [metrics[i]]
                if i + 1 < len(metrics):
                    row.append(metrics[i + 1])
                else:
                    row.append(('', ''))
                table_data.append(row)
            
            # Flatten the table data
            table_data = [[f"{k}: {v}" for k, v in row] for row in table_data]
            
            # Create and style the table
            table = Table(table_data, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "Courier"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            
            story.append(table)
            
            # Add note if present
            if "note" in halstead:
                story.append(Spacer(1, 6))
                story.append(Paragraph(f"<i>{halstead['note']}</i>", styles["Italic"]))
            
            story.append(Spacer(1, 12))
    
    # Add timestamp
    from datetime import datetime
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"<i>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        styles["Italic"]
    ))
    
    # Build the PDF
    doc.build(story)

# -------- Markdown Generator -------- #

def save_markdown(report: dict, md_path: str = "outputs/report.md") -> None:
    lines = []
    lines.append(f"# Code Documentation Report\n")
    lines.append(f"**File**: {report['file']}\n")

    lines.append(f"## Summary\n{report['summary']['paragraph']}\n")

    if report["summary"]["points"]:
        lines.append("## Details")
        for p in report["summary"]["points"]:
            lines.append(f"- {p}")
        lines.append("")

    if report.get("samples"):
        lines.append("## Sample Input/Output")
        lines.append("| Function | Input | Output |")
        lines.append("|----------|-------|--------|")
        for fn, io in report["samples"].items():
            lines.append(f"| {fn} | {io.get('input','-')} | {io.get('output','-')} |")
        lines.append("")

    lines.append("## Parsed Information")
    for line in format_parsed_info(report["parsed_info"], for_pdf=False):
        lines.append(line)
    lines.append("")

    lines.append("## Complexity Information")
    for c in report["complexity_info"].get("cyclomatic_complexity", []):
        lines.append(f"- {c['name']}: {map_complexity_to_big_o(c['complexity'])}")
    mi = report["complexity_info"].get("maintainability_index")
    if mi is None:
        lines.append("- Maintainability Index: not available")
    else:
        lines.append(f"- Maintainability Index: {mi:.2f}")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# -------- Main -------- #

def generate_report(code: str, output_dir: str = "outputs", display_name: str = None) -> dict:
    """
    Generate a code documentation report for the given source file.

    Args:
        code: Path to the source code file
        output_dir: Directory to save the output files
        display_name: Name to show as the report title. Defaults to the
            file's basename; callers that write to a temporary file should
            pass the name the user knows it by.

    Returns:
        Dictionary containing the complete report
    """
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Parse the code using the code content directly
        from analyzer.code_parser import parse_code
        parsed_info = parse_code(code)
        
        if not parsed_info:
            raise ValueError("Failed to parse the source code")
        
        # Analyze complexity using the code content directly
        from analyzer.complexity import analyze_complexity
        complexity_info = analyze_complexity(code)
        
        # Initialize samples as empty - we're disabling sample I/O execution
        samples = {}
        
        # Summaries are built from the parsed structure.
        #
        # The CodeT5 summarizer (analyzer/summarizer.py) is deliberately not
        # used: its output never passed is_bad_summary(), so build_paragraph()
        # produced every summary anyway while torch + the 232MB checkpoint cost
        # ~30s per request. See Readme "AI summarizer" before re-enabling.
        summary_text = build_paragraph(parsed_info)


        # Format the summary
        formatted_summary = format_summary(summary_text, parsed_info, complexity_info, samples)
        
        # Build the report
        report = {
            "file": display_name or os.path.basename(code),
            "summary": formatted_summary,
            "parsed_info": parsed_info,
            "complexity_info": complexity_info,
            "samples": samples
        }
        
        # Save JSON report
        with open(os.path.join(output_dir, "report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
        
        # Generate PDF report
        save_pdf(report, pdf_path=os.path.join(output_dir, "report.pdf"))
        
        # Generate Markdown report
        save_markdown(report, md_path=os.path.join(output_dir, "report.md"))
        
        return report
        
    except Exception as e:
        print(f"Error in generate_report: {str(e)}")
        raise  # Re-raise the exception to be handled by the caller
