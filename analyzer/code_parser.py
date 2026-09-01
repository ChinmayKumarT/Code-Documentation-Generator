# analyzer/code_parser.py
import os
from typing import Dict, List, Any, Optional
import ast
import re

class BaseParser:
    """Base class for all language parsers"""
    def parse(self, filepath: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse the given file and return structured code information"""
        raise NotImplementedError("Subclasses must implement parse method")

class PythonParser(BaseParser):
    """Parser for Python source code"""
    def parse(self, filepath: str) -> Dict[str, List[Dict[str, Any]]]:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        code_info = {
            "classes": [],
            "functions": [],
            "variables": []
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                code_info["classes"].append({
                    "name": node.name,
                    "methods": methods,
                    "type": "class"
                })
            elif isinstance(node, ast.FunctionDef):
                args = [a.arg for a in node.args.args]
                code_info["functions"].append({
                    "name": node.name,
                    "args": args,
                    "type": "function"
                })
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        code_info["variables"].append({
                            "name": target.id,
                            "type": "variable"
                        })
        return code_info

class JavaParser(BaseParser):
    """Parser for Java source code"""
    def parse(self, filepath: str) -> Dict[str, List[Dict[str, Any]]]:
        code_info = {
            "classes": [],
            "methods": [],
            "fields": []
        }
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple regex patterns (can be enhanced for more complex cases)
        class_pattern = r'\b(?:public|private|protected|static|final|abstract|transient|synchronized|volatile|strictfp)?\s*class\s+(\w+)'
        method_pattern = r'(?:public|private|protected|static|final|native|synchronized|abstract|transient)+\s+[\w\<\>\[\]]+\s+(\w+)\s*\([^{}]*\)\s*(?:throws [\w\s,]+)?\s*\{'
        field_pattern = r'(?:public|private|protected|static|final|transient|volatile)+\s+[\w\<\>\[\]]+\s+(\w+)\s*(?:=\s*[^;]+)?;'
        
        # Find classes
        for match in re.finditer(class_pattern, content):
            code_info["classes"].append({
                "name": match.group(1),
                "type": "class"
            })
            
        # Find methods
        for match in re.finditer(method_pattern, content):
            code_info["methods"].append({
                "name": match.group(1),
                "type": "method"
            })
            
        # Find fields
        for match in re.finditer(field_pattern, content):
            code_info["fields"].append({
                "name": match.group(1),
                "type": "field"
            })
            
        return code_info

class CParser(BaseParser):
    """Parser for C source code"""
    def parse(self, filepath: str) -> Dict[str, List[Dict[str, Any]]]:
        code_info = {
            "functions": [],
            "structs": [],
            "variables": []
        }
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Simple patterns (can be enhanced)
        function_pattern = r'\b(?:int|float|double|char|void|struct\s+\w+)\s+([*\s]*\w+)\s*\('  # Matches function declarations
        struct_pattern = r'\bstruct\s+(\w+)\s*\{'
        variable_pattern = r'\b(?:int|float|double|char|void|struct\s+\w+)\s+([*\s]*\w+)\s*(?:\[\d*\])?\s*(?:=\s*[^;]+)?;'
        
        # Find functions
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1).strip()
            if func_name and not any(c in func_name for c in ';{'):
                code_info["functions"].append({
                    "name": func_name,
                    "type": "function"
                })
                
        # Find structs
        for match in re.finditer(struct_pattern, content):
            code_info["structs"].append({
                "name": match.group(1),
                "type": "struct"
            })
            
        # Find global variables
        for match in re.finditer(variable_pattern, content):
            var_name = match.group(1).strip()
            if var_name and not any(c in var_name for c in ';{'):
                code_info["variables"].append({
                    "name": var_name,
                    "type": "variable"
                })
                
        return code_info

class CppParser(CParser):
    """Parser for C++ source code (extends C parser with C++ specific features)"""
    def parse(self, filepath: str) -> Dict[str, List[Dict[str, Any]]]:
        code_info = super().parse(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Add C++ specific patterns
        class_pattern = r'\bclass\s+(\w+)'
        method_pattern = r'\b(?:\w+::)*\s*(?:virtual\s+)?(?:\w+\s+)*(?:\w+::)*(~?\w+)\s*\('  # Matches method declarations
        
        # Find classes
        for match in re.finditer(class_pattern, content):
            code_info.setdefault("classes", []).append({
                "name": match.group(1),
                "type": "class"
            })
            
        # Find methods (including class methods)
        for match in re.finditer(method_pattern, content):
            method_name = match.group(1)
            if method_name and not any(c in method_name for c in ';{'):
                code_info.setdefault("methods", []).append({
                    "name": method_name,
                    "type": "method"
                })
                
        return code_info

class JavaScriptParser(BaseParser):
    """Parser for JavaScript source code"""
    def parse(self, filepath: str) -> Dict[str, List[Dict[str, Any]]]:
        code_info = {
            "functions": [],
            "classes": [],
            "variables": []
        }
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Function patterns (supports various function declaration styles)
        function_patterns = [
            r'\bfunction\s+(\w+)',  # function name()
            r'\b(\w+)\s*=\s*\([^)]*\)\s*=>',  # name = () =>
            r'\b(\w+)\s*:\s*function\s*\('  # name: function(
        ]
        
        # Class pattern
        class_pattern = r'\bclass\s+(\w+)'
        
        # Variable patterns
        variable_pattern = r'\b(?:const|let|var)\s+([a-zA-Z_$][\w$]*)'
        
        # Find functions
        for pattern in function_patterns:
            for match in re.finditer(pattern, content):
                code_info["functions"].append({
                    "name": match.group(1),
                    "type": "function"
                })
                
        # Find classes
        for match in re.finditer(class_pattern, content):
            code_info["classes"].append({
                "name": match.group(1),
                "type": "class"
            })
            
        # Find variables
        for match in re.finditer(variable_pattern, content):
            code_info["variables"].append({
                "name": match.group(1),
                "type": "variable"
            })
            
        return code_info

def get_parser(filepath: str) -> Optional[BaseParser]:
    """Get the appropriate parser based on file extension"""
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    parsers = {
        '.py': PythonParser(),
        '.java': JavaParser(),
        '.c': CParser(),
        '.cpp': CppParser(),
        '.cc': CppParser(),
        '.h': CppParser(),
        '.hpp': CppParser(),
        '.js': JavaScriptParser(),
        '.ts': JavaScriptParser()  # TypeScript uses similar syntax to JavaScript for basic parsing
    }
    
    return parsers.get(ext)

def parse_code(filepath: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Parse a source code file and return structured information.
    
    Args:
        filepath: Path to the source code file
        
    Returns:
        Dictionary containing parsed code structure
        
    Raises:
        ValueError: If the file type is not supported
    """
    parser = get_parser(filepath)
    if not parser:
        raise ValueError(f"Unsupported file type: {filepath}")
    
    return parser.parse(filepath)
