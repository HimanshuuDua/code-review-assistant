"""HuggingFace Inference API clients for base and specialized review models."""

from __future__ import annotations

import json
import re
import time

import httpx

from backend.config import settings
from backend.schemas import CommentType, ReviewComment, ReviewRequest, Severity

COMMENT_TYPES = {"bug", "security", "performance", "style", "suggestion", "refactor", "question"}


def _headers() -> dict[str, str]:
    if settings.hf_token:
        return {"Authorization": f"Bearer {settings.hf_token}"}
    return {}


async def _post_inference(model_id: str, payload: dict) -> str:
    url = f"{settings.hf_inference_api_url}/{model_id}"
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=_headers(), json=payload)
        if response.status_code == 503:
            # Model loading — brief retry
            await client.post(url, headers=_headers(), json=payload)
            response = await client.post(url, headers=_headers(), json=payload)
        response.raise_for_status()
        data = response.json()

    if isinstance(data, list) and data:
        item = data[0]
        return item.get("generated_text") or item.get("summary_text") or str(item)
    if isinstance(data, dict):
        return data.get("generated_text") or data.get("summary_text") or json.dumps(data)
    return str(data)


def _text_to_comments(text: str, default_type: str = "suggestion") -> list[ReviewComment]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("["), text.rfind("]")
    if start != -1 and end != -1:
        try:
            items = json.loads(text[start : end + 1])
            comments: list[ReviewComment] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                ctype = item.get("type", default_type)
                if ctype not in COMMENT_TYPES:
                    ctype = default_type
                sev = item.get("severity", "medium")
                if sev not in {"high", "medium", "low"}:
                    sev = "medium"
                comments.append(
                    ReviewComment(
                        type=CommentType(ctype),
                        severity=Severity(sev),
                        message=str(item.get("message", "")),
                        line=item.get("line"),
                    )
                )
            if comments:
                return comments
        except (json.JSONDecodeError, ValueError):
            pass

    sentences = [s.strip() for s in re.split(r"[\n.]+", text) if len(s.strip()) > 10]
    if not sentences:
        sentences = [text[:500]] if text else ["No specific issues identified."]
    return [
        ReviewComment(
            type=CommentType(default_type),
            severity=Severity.MEDIUM if default_type in ("bug", "security") else Severity.LOW,
            message=s[:500],
        )
        for s in sentences[:3]
    ]


async def generate_base_mistral(request: ReviewRequest, prompt: str) -> tuple[str, float]:
    start = time.perf_counter()
    raw = await _post_inference(
        settings.base_model_id,
        {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 400, "temperature": 0.3, "return_full_text": False},
        },
    )
    return raw, (time.perf_counter() - start) * 1000


async def generate_codereviewer(request: ReviewRequest) -> tuple[str, list[ReviewComment], float]:
    """Microsoft CodeReviewer — pretrained on real PR review data."""
    code_input = (
        f"Review this {request.language} code and list issues:\n"
        f"```{request.language}\n{request.code}\n```"
    )
    start = time.perf_counter()
    raw = await _post_inference(
        settings.codereviewer_model_id,
        {"inputs": code_input, "parameters": {"max_new_tokens": 256, "temperature": 0.2}},
    )
    latency = (time.perf_counter() - start) * 1000
    comments = _text_to_comments(raw, default_type="suggestion")
    return raw, comments, latency


async def generate_finetuned_lora(prompt: str, model_id: str) -> tuple[str, float]:
    start = time.perf_counter()
    raw = await _post_inference(
        model_id,
        {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 400, "temperature": 0.3, "return_full_text": False},
        },
    )
    return raw, (time.perf_counter() - start) * 1000
