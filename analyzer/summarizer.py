# analyzer/summarizer.py
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

class CodeSummarizer:
    def __init__(self, model_dir=None):
        if model_dir is None:
            model_dir = Path(__file__).resolve().parent.parent / "codet5-small"

        self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        self.model = AutoModelForSeq2SeqLM.from_pretrained(str(model_dir))

    def summarize_code(self, code: str, max_length: int = 128) -> str:
        # Minimal prompt works best for CodeT5
        prompt = "summarize: " + code

        inputs = self.tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=512
        )

        outputs = self.model.generate(
            inputs["input_ids"],
            max_length=max_length,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            temperature=0.7,
        )

        summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Fallback if junk
        if not summary.strip() or summary.strip().lower() in ["=", "0", "function", "none"]:
            summary = ""

        return summary


def summarize_code(code: str) -> str:
    return CodeSummarizer().summarize_code(code)
