# Code Review Assistant

An AI-powered code review assistant fine-tuned with LoRA on real pull-request review data. Paste a code snippet and get structured review comments — with a side-by-side comparison of **base Mistral 7B** vs **your fine-tuned model**.

## What It Does

| Problem | Solution |
|---------|----------|
| Generic LLMs give vague feedback | Fine-tuned model gives specific, actionable comments |
| No way to prove improvement | Before/After side-by-side demo |
| Training is opaque | Documented Colab notebook with real metrics |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────────┐
│  React UI   │────▶│  FastAPI     │────▶│  Mistral 7B (base)      │
│  + Tailwind │     │  Backend     │     │  + LoRA adapter (tuned) │
└─────────────┘     └──────────────┘     └─────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │  Colab NB   │  LoRA fine-tune on CodeReviewer data
                    │  Evaluation │  BLEU + structured comment metrics
                    └─────────────┘
```

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| Base Model | Mistral 7B Instruct | Small, fast, open-source |
| Fine-tuning | LoRA via PEFT + TRL | Memory-efficient, runs on free T4 GPU |
| Training | Google Colab / Kaggle | Free T4/A100 GPUs |
| Dataset | [github-codereview](https://huggingface.co/datasets/ronantakizawa/github-codereview) | Real PR review comments from top repos |
| Backend | FastAPI | Simple model serving |
| Frontend | React + Tailwind | Clean side-by-side comparison UI |
| Hosting | HuggingFace Hub | Free model storage & inference |

## Quick Start

### 1. Fine-tune the model (Colab)

Open `notebooks/finetune_codereviewer_lora.ipynb` in Google Colab:

1. Runtime → Change runtime type → **T4 GPU**
2. Set your HuggingFace token in the first cell
3. Run all cells (~2-4 hours on T4)
4. Push the LoRA adapter to HuggingFace Hub

### 2. Run the backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp ../.env.example ../.env    # edit with your HF token & model ID
uvicorn main:app --reload --port 8000
```

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — paste code, click **Review**, see base vs fine-tuned side by side.

### 4. Evaluate

```bash
cd evaluation
pip install -r requirements.txt
python evaluate.py --model-id your-username/code-review-mistral-lora
```

## Project Structure

```
code-review-assistant/
├── notebooks/
│   └── finetune_codereviewer_lora.ipynb   # LoRA training (start here)
├── backend/
│   ├── main.py                            # FastAPI server
│   ├── config.py
│   ├── schemas.py
│   └── services/reviewer.py               # Model inference
├── frontend/
│   └── src/                               # React + Tailwind UI
├── evaluation/
│   └── evaluate.py                        # BLEU & quality metrics
└── scripts/
    └── prepare_data.py                      # Dataset preprocessing
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/review` | Review code with both models |
| `POST` | `/api/review/base` | Base Mistral only |
| `POST` | `/api/review/finetuned` | Fine-tuned model only |
| `GET` | `/api/health` | Health check |

### Example request

```json
POST /api/review
{
  "code": "def divide(a, b):\n    return a / b",
  "language": "python"
}
```

### Example response

```json
{
  "base_model": {
    "comments": [
      {"type": "suggestion", "severity": "low", "message": "Consider adding type hints."}
    ],
    "raw_response": "..."
  },
  "finetuned_model": {
    "comments": [
      {"type": "bug", "severity": "high", "message": "Division by zero: add a guard when b == 0."}
    ],
    "raw_response": "..."
  }
}
```

## Demo Mode

Without a GPU or HuggingFace token, the backend runs in **demo mode** with realistic sample responses so you can develop the UI immediately. Set `INFERENCE_MODE=demo` in `.env`.

## Training Details

- **Dataset**: 167K human-written review triplets from top GitHub repos
- **Method**: QLoRA (4-bit) + LoRA rank 16 on attention + MLP layers
- **Prompt format**: Mistral Instruct chat template
- **Output**: Structured JSON with `type`, `severity`, `message` per comment
- **Metrics**: BLEU-4, comment-type accuracy, human preference (A/B)

## License

MIT — dataset follows original licenses (Apache 2.0 for CodeReviewer, MIT for github-codereview).
