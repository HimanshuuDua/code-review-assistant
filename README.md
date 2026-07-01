# Code Review Assistant — Complete Project Guide

AI-powered code review with **base Mistral 7B** vs **specialized model** (CodeReviewer / your LoRA), side-by-side UI, review history, and admin dashboard.

## Live URLs

| Service | URL |
|---------|-----|
| **App** | https://code-review-assistant-eight.vercel.app |
| **Admin** | https://code-review-assistant-eight.vercel.app/admin |
| **GitHub** | https://github.com/HimanshuuDua/code-review-assistant |

## What's Complete

- React + Tailwind UI with side-by-side comparison
- FastAPI backend on Vercel (serverless)
- **Hybrid inference**: Mistral 7B (base) + Microsoft CodeReviewer (specialized) via HuggingFace API, with demo fallback
- Review history storage (SQLite local / `/tmp` on Vercel / Postgres via `DATABASE_URL`)
- Admin dashboard — who reviewed what, issue types, CSV export
- GitHub OAuth (optional — set `GITHUB_CLIENT_ID` + `GITHUB_CLIENT_SECRET`)
- Rate limiting (30 req/min per IP on `/api/review`)
- 15+ backend tests, 5 Playwright E2E tests, GitHub Actions CI
- LoRA fine-tuning Colab notebook + HF Jobs training workflow

## Inference Modes

| Mode | Description |
|------|-------------|
| `hybrid` | **Production default** — HF API for Mistral + CodeReviewer, demo fallback |
| `demo` | Rule-based responses (offline dev) |
| `huggingface` | Both models via HF Inference API |
| `local` | GPU required — 4-bit QLoRA loading |

## Quick Start (Local)

```bash
# Backend
cd backend && .venv\Scripts\activate
pip install -r requirements-lite.txt
cd .. && set PYTHONPATH=.
uvicorn backend.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

## Fine-tune Your Own LoRA (Optional)

### Option A: Google Colab (free T4)
1. Open `notebooks/finetune_codereviewer_lora.ipynb` in Colab
2. Set `HF_TOKEN` + `HF_USERNAME`, enable T4 GPU
3. Run all cells (~2-4 hours)
4. Set `FINETUNED_MODEL_ID=your-username/code-review-mistral-lora` on Vercel

### Option B: GitHub Actions + HF Jobs
1. Add `HF_TOKEN` secret to GitHub repo
2. Actions → **Fine-tune Model** → Run workflow
3. Monitor with `hf jobs ps`

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `INFERENCE_MODE` | `hybrid` \| `demo` \| `huggingface` \| `local` |
| `HF_TOKEN` | HuggingFace API (enables real model inference) |
| `FINETUNED_MODEL_ID` | Your LoRA adapter on HF Hub |
| `DATABASE_URL` | Postgres connection (Neon recommended for Vercel) |
| `ADMIN_API_KEY` | Admin dashboard auth |
| `GITHUB_CLIENT_ID` | Optional GitHub OAuth |
| `APP_BASE_URL` | Production URL for OAuth redirects |

## Persistent Storage on Vercel (Neon)

1. Vercel Dashboard → Storage → Create Database → Neon Postgres
2. `DATABASE_URL` is auto-injected
3. Redeploy — review history persists across deployments

## API

| Endpoint | Auth | Description |
|----------|------|-------------|
| `POST /api/review` | — | Compare base vs specialized |
| `GET /api/admin/reviews` | `X-Admin-Key` | Review history |
| `GET /api/admin/reviews/export` | `X-Admin-Key` | CSV download |
| `GET /api/admin/stats` | `X-Admin-Key` | Totals |
| `GET /api/auth/github` | — | GitHub OAuth (if configured) |

## Tests

```bash
# Backend
PYTHONPATH=. pytest backend/tests -v

# E2E
npm run test:e2e

# Evaluation
python evaluation/evaluate.py --samples 100 --mode demo
```

## Architecture

```
User → React UI → FastAPI → Hybrid Inference
                              ├─ Base: Mistral 7B (HF API)
                              └─ Specialized: CodeReviewer / your LoRA
                    ↓
              SQLite / Postgres (review history)
                    ↓
              Admin Dashboard + CSV Export
```
