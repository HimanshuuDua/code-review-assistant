#!/usr/bin/env python3
"""
LoRA fine-tuning script for HuggingFace Jobs or local GPU.

Usage (HF Jobs — requires `hf auth login`):
    hf jobs run --flavor t4-medium --env HF_TOKEN=$HF_TOKEN --env HF_USERNAME=your-username \\
        python:3.12 scripts/train.py

Usage (local GPU):
    python scripts/train.py --hf-username your-username
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from datasets import Dataset, load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
from trl import SFTTrainer

SYSTEM = """You are a senior software engineer performing a code review.
Analyze the provided code and return a JSON array of review comments.
Each comment must have: type (bug|security|performance|style|suggestion|refactor|question), severity (high|medium|low), message, and optional line.
Return ONLY valid JSON."""

BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "train.jsonl"


def format_example(row: dict) -> dict:
    comment_type = row.get("comment_type", "suggestion")
    severity = (
        "high"
        if comment_type in ("bug", "security")
        else "medium"
        if comment_type == "performance"
        else "low"
    )
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
    user = f"""Language: {row.get('language', 'unknown')}
Code to review:
```
{row['before_code']}
```

Return a JSON array of review comments."""
    return {"text": f"<s>[INST] {SYSTEM}\n\n{user} [/INST] {target}</s>"}


def load_training_data(max_samples: int) -> tuple[Dataset, Dataset]:
    if DATA_FILE.exists():
        print(f"Loading prepared data from {DATA_FILE}")
        rows = []
        with DATA_FILE.open(encoding="utf-8") as f:
            for line in f:
                rows.append(json.loads(line))
                if len(rows) >= max_samples:
                    break
        dataset = Dataset.from_list(rows)
    else:
        print("Downloading github-codereview from HuggingFace...")
        raw = load_dataset("ronantakizawa/github-codereview", split="train", streaming=True)
        examples = []
        for row in raw:
            if row.get("is_negative") or not row.get("reviewer_comment"):
                continue
            examples.append(format_example(row))
            if len(examples) >= max_samples:
                break
        dataset = Dataset.from_list(examples)

    split = dataset.train_test_split(test_size=0.05, seed=42)
    return split["train"], split["test"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hf-username", default=os.environ.get("HF_USERNAME", "your-username"))
    parser.add_argument("--hf-token", default=os.environ.get("HF_TOKEN", ""))
    parser.add_argument("--max-samples", type=int, default=5000)
    parser.add_argument("--max-seq-length", type=int, default=1024)
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--output-dir", default="./checkpoints")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit(
            "No GPU detected. Use Google Colab (notebooks/finetune_codereviewer_lora.ipynb) "
            "or HuggingFace Jobs: hf jobs run --flavor t4-medium python:3.12 scripts/train.py"
        )

    hf_token = args.hf_token or None
    output_repo = f"{args.hf_username}/code-review-mistral-lora"

    print(f"GPU: {torch.cuda.get_device_name(0)}")
    train_dataset, eval_dataset = load_training_data(args.max_samples)
    print(f"Train: {len(train_dataset)} | Eval: {len(eval_dataset)}")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, token=hf_token)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        token=hf_token,
    )
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=8,
        optim="paged_adamw_8bit",
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=25,
        eval_strategy="steps",
        eval_steps=100,
        save_steps=200,
        save_total_limit=2,
        fp16=False,
        bf16=torch.cuda.is_bf16_supported(),
        max_grad_norm=0.3,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        peft_config=lora_config,
        processing_class=tokenizer,
        args=training_args,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        packing=False,
    )

    print("Starting training...")
    trainer.train()
    print("Training complete!")

    print(f"Pushing adapter to https://huggingface.co/{output_repo}")
    trainer.model.push_to_hub(output_repo, token=hf_token)
    tokenizer.push_to_hub(output_repo, token=hf_token)
    print("Done!")


if __name__ == "__main__":
    main()
