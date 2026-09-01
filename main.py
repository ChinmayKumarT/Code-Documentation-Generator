# main.py
import sys
from analyzer.report_generator import generate_report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <path-to-code-file>")
        sys.exit(1)

    filepath = sys.argv[1]
    report = generate_report(filepath)

    print("Report generated:")
    print("JSON -> report.json")
    print("PDF  -> report.pdf")
