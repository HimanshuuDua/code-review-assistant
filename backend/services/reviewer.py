import json
import re
import time
from typing import Any

from config import settings
from schemas import CommentType, ModelReviewResult, ReviewComment, ReviewRequest, Severity

SYSTEM_PROMPT = """You are a senior software engineer performing a code review.
Analyze the provided code and return a JSON array of review comments.
Each comment must have: type (bug|security|performance|style|suggestion|refactor|question), severity (high|medium|low), message (specific actionable feedback), and optional line number.
Be specific — point out exact issues with explanations, not vague suggestions.
Return ONLY valid JSON, no markdown fences."""

REVIEW_TEMPLATE = """<s>[INST] {system}

Language: {language}
{context_block}
Code to review:
```
{code}
```

Return a JSON array of review comments. [/INST]"""


def _build_prompt(request: ReviewRequest) -> str:
    context_block = f"Context: {request.context}" if request.context else ""
    return REVIEW_TEMPLATE.format(
        system=SYSTEM_PROMPT,
        language=request.language,
        context_block=context_block,
        code=request.code,
    )


def _parse_comments(raw: str) -> list[ReviewComment]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()

    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return [
            ReviewComment(
                type=CommentType.SUGGESTION,
                severity=Severity.LOW,
                message=raw.strip()[:500] or "No structured comments parsed.",
            )
        ]

    try:
        items = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return [
            ReviewComment(
                type=CommentType.SUGGESTION,
                severity=Severity.LOW,
                message=raw.strip()[:500],
            )
        ]

    comments: list[ReviewComment] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            comments.append(
                ReviewComment(
                    type=CommentType(item.get("type", "suggestion")),
                    severity=Severity(item.get("severity", "low")),
                    message=str(item.get("message", "")),
                    line=item.get("line"),
                )
            )
        except ValueError:
            comments.append(
                ReviewComment(
                    type=CommentType.SUGGESTION,
                    severity=Severity.LOW,
                    message=str(item.get("message", item)),
                )
            )
    return comments or [
        ReviewComment(type=CommentType.SUGGESTION, severity=Severity.LOW, message="No issues found.")
    ]


def _demo_response(request: ReviewRequest, model_name: str, is_finetuned: bool) -> ModelReviewResult:
    code = request.code.lower()

    if is_finetuned:
        comments: list[ReviewComment] = []
        if "password" in code and ("=" in code or "input" in code):
            comments.append(
                ReviewComment(
                    type=CommentType.SECURITY,
                    severity=Severity.HIGH,
                    message="Hardcoded or plaintext password handling detected. Use environment variables and hash secrets with bcrypt/argon2.",
                    line=1,
                )
            )
        if re.search(r"/\s*\w+", request.code) and "if" not in code and "try" not in code:
            comments.append(
                ReviewComment(
                    type=CommentType.BUG,
                    severity=Severity.HIGH,
                    message="Division without zero-check will raise ZeroDivisionError. Guard with `if divisor == 0` or use safe division.",
                    line=2,
                )
            )
        if "eval(" in code or "exec(" in code:
            comments.append(
                ReviewComment(
                    type=CommentType.SECURITY,
                    severity=Severity.HIGH,
                    message="Avoid eval()/exec() on user input — arbitrary code execution risk (CWE-94).",
                )
            )
        if "select" in code and "+" in code and "?" not in code:
            comments.append(
                ReviewComment(
                    type=CommentType.SECURITY,
                    severity=Severity.HIGH,
                    message="String-concatenated SQL query is vulnerable to SQL injection. Use parameterized queries.",
                )
            )
        if not comments:
            comments.append(
                ReviewComment(
                    type=CommentType.STYLE,
                    severity=Severity.LOW,
                    message="Code looks reasonable. Consider adding type hints and docstrings for public functions.",
                )
            )
        raw = json.dumps([c.model_dump() for c in comments], indent=2)
    else:
        comments = [
            ReviewComment(
                type=CommentType.SUGGESTION,
                severity=Severity.LOW,
                message="Consider improving error handling in this function.",
            ),
            ReviewComment(
                type=CommentType.STYLE,
                severity=Severity.LOW,
                message="The code could be more readable with better naming.",
            ),
            ReviewComment(
                type=CommentType.SUGGESTION,
                severity=Severity.LOW,
                message="You might want to add input validation.",
            ),
        ]
        raw = "The code looks okay but could be improved. Consider adding error handling and validation."

    return ModelReviewResult(model_name=model_name, comments=comments, raw_response=raw, latency_ms=120.0)


class ReviewerService:
    def __init__(self) -> None:
        self._base_pipeline: Any = None
        self._finetuned_pipeline: Any = None
        self._loaded = False

    def _ensure_local_models(self) -> None:
        if self._loaded or settings.inference_mode != "local":
            return

        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

        tokenizer = AutoTokenizer.from_pretrained(settings.base_model_id, token=settings.hf_token or None)
        tokenizer.pad_token = tokenizer.eos_token

        base_model = AutoModelForCausalLM.from_pretrained(
            settings.base_model_id,
            quantization_config=bnb_config,
            device_map="auto",
            token=settings.hf_token or None,
        )

        self._base_pipeline = pipeline(
            "text-generation",
            model=base_model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.3,
            return_full_text=False,
        )

        finetuned_base = AutoModelForCausalLM.from_pretrained(
            settings.base_model_id,
            quantization_config=bnb_config,
            device_map="auto",
            token=settings.hf_token or None,
        )
        finetuned_model = PeftModel.from_pretrained(finetuned_base, settings.finetuned_model_id)
        self._finetuned_pipeline = pipeline(
            "text-generation",
            model=finetuned_model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.3,
            return_full_text=False,
        )
        self._loaded = True

    def _generate_local(self, prompt: str, use_finetuned: bool) -> tuple[str, float]:
        self._ensure_local_models()
        pipe = self._finetuned_pipeline if use_finetuned else self._base_pipeline
        if pipe is None:
            raise RuntimeError("Local models not loaded")

        start = time.perf_counter()
        result = pipe(prompt)[0]["generated_text"]
        latency = (time.perf_counter() - start) * 1000
        return result, latency

    async def _generate_hf_api(self, prompt: str, model_id: str) -> tuple[str, float]:
        import httpx

        headers = {"Authorization": f"Bearer {settings.hf_token}"} if settings.hf_token else {}
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 512, "temperature": 0.3, "return_full_text": False},
        }

        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.hf_inference_api_url}/{model_id}",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        latency = (time.perf_counter() - start) * 1000
        if isinstance(data, list) and data:
            raw = data[0].get("generated_text", str(data[0]))
        elif isinstance(data, dict):
            raw = data.get("generated_text", json.dumps(data))
        else:
            raw = str(data)
        return raw, latency

    async def review(self, request: ReviewRequest, use_finetuned: bool = False) -> ModelReviewResult:
        model_name = settings.finetuned_model_id if use_finetuned else settings.base_model_id
        prompt = _build_prompt(request)

        if settings.inference_mode == "demo":
            return _demo_response(request, model_name, is_finetuned=use_finetuned)

        if settings.inference_mode == "local":
            raw, latency = self._generate_local(prompt, use_finetuned=use_finetuned)
        elif settings.inference_mode == "huggingface":
            raw, latency = await self._generate_hf_api(prompt, model_name)
        else:
            return _demo_response(request, model_name, is_finetuned=use_finetuned)

        comments = _parse_comments(raw)
        return ModelReviewResult(
            model_name=model_name,
            comments=comments,
            raw_response=raw,
            latency_ms=latency,
        )

    async def compare(self, request: ReviewRequest) -> tuple[ModelReviewResult, ModelReviewResult]:
        base = await self.review(request, use_finetuned=False)
        finetuned = await self.review(request, use_finetuned=True)
        return base, finetuned


reviewer_service = ReviewerService()
