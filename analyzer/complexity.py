# analyzer/complexity.py
import os
from typing import Dict, List, Any, Optional
from radon.complexity import cc_visit
from radon.metrics import mi_visit, h_visit

def analyze_complexity(filepath: str) -> dict:
    """
    Analyze code complexity using appropriate methods based on file type.
    For Python files, uses Radon for detailed analysis.
    For other languages, provides basic analysis based on code structure.
    """
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    results = {
        "cyclomatic_complexity": [],
        "maintainability_index": None,
        "halstead_metrics": None
    }

    if ext == '.py':
        # Full analysis for Python files
        try:
            # Cyclomatic Complexity
            results["cyclomatic_complexity"] = [
                {"name": block.name, "complexity": block.complexity}
                for block in cc_visit(source)
            ]
            
            # Maintainability Index
            results["maintainability_index"] = mi_visit(source, True)
            
            # Halstead Metrics
            halstead = h_visit(source)
            results["halstead_metrics"] = {
                "h1": halstead.h1,
                "h2": halstead.h2,
                "N1": halstead.N1,
                "N2": halstead.N2,
                "vocabulary": halstead.vocabulary,
                "length": halstead.length,
                "volume": halstead.volume,
                "difficulty": halstead.difficulty,
                "effort": halstead.effort,
                "time": halstead.time,
                "bugs": halstead.bugs
            }
            
        except Exception as e:
            results["error"] = f"Python analysis error: {str(e)}"
            
    else:
        # Basic analysis for non-Python files
        try:
            # Simple cyclomatic complexity estimation based on code structure
            complexity = 1  # Base complexity
            
            # Count control flow statements (very basic approach)
            control_flow_keywords = [
                'if', 'else', 'for', 'while', 'case', 'default', 'try', 'catch',
                '&&', '||', '?', ':', 'for', 'foreach', 'break', 'continue', 'goto'
            ]
            
            for keyword in control_flow_keywords:
                complexity += source.count(f' {keyword} ') + source.count(f'\t{keyword} ') + \
                             source.count(f'\n{keyword} ') + source.count(f'({keyword}') + \
                             source.count(f'{keyword}(')
            
            # Add a point for each function/method
            function_keywords = ['def ', 'function ', 'fn ', 'func ', 'public ', 'private ', 'protected ']
            for keyword in function_keywords:
                complexity += source.count(keyword)
            
            # Estimate maintainability index (0-100 scale)
            line_count = len(source.splitlines())
            maintainability = max(0, min(100, 100 - (complexity / 10) - (line_count / 100)))
            
            results["cyclomatic_complexity"].append({
                "name": "file_complexity",
                "complexity": complexity
            })
            
            results["maintainability_index"] = maintainability
            
            # Basic halstead-like metrics
            operators = sum(source.count(op) for op in ['+', '-', '*', '/', '%', '=', '>', '<', '!'])
            operands = sum(source.count(op) for op in [';', ',', '(', ')', '[', ']', '{', '}'])
            
            results["halstead_metrics"] = {
                "operators": operators,
                "operands": operands,
                "volume": operators + operands,
                "note": "Basic metrics only. For detailed analysis, use a language-specific tool."
            }
            
        except Exception as e:
            results["error"] = f"Basic analysis error: {str(e)}"
            results["cyclomatic_complexity"] = [{"name": "error", "complexity": 0}]
            results["maintainability_index"] = 0
            results["halstead_metrics"] = {}
    
    return results
