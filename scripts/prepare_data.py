"""
Preprocess github-codereview dataset into Mistral Instruct training format.

Usage:
    python prepare_data.py --output data/train.jsonl --max-samples 5000
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import load_dataset

SYSTEM = """You are a senior software engineer performing a code review.
Analyze the provided code and return a JSON array of review comments.
Each comment must have: type, severity, message, and optional line.
Return ONLY valid JSON."""


def format_training_example(row: dict) -> dict:
    comment_type = row.get("comment_type", "suggestion")
    severity = "high" if comment_type in ("bug", "security") else "medium" if comment_type in ("performance",) else "low"

    target = json.dumps(
        [
            {
                "type": comment_type,
                "severity": severity,
                "message": row["reviewer_comment"],
                "line": row.get("comment_line") or None,
            }
        ],
        ensure_ascii=False,
    )

    language = row.get("language", "unknown")
    user_block = f"""Language: {language}
Code to review:
```
{row['before_code']}
```

Return a JSON array of review comments."""

    text = f"<s>[INST] {SYSTEM}\n\n{user_block} [/INST] {target}</s>"
    return {"text": text, "comment_type": comment_type, "language": language}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/train.jsonl")
    parser.add_argument("--max-samples", type=int, default=5000)
    parser.add_argument("--include-negatives", action="store_true")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Loading ronantakizawa/github-codereview...")
    dataset = load_dataset("ronantakizawa/github-codereview", split="train", streaming=True)

    count = 0
    with output_path.open("w", encoding="utf-8") as f:
        for row in dataset:
            if not args.include_negatives and row.get("is_negative"):
                continue
            if not row.get("reviewer_comment"):
                continue
            example = format_training_example(row)
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
            count += 1
            if count >= args.max_samples:
                break

    print(f"Wrote {count} examples to {output_path}")


if __name__ == "__main__":
    main()
