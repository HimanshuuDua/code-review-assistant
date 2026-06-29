# Workflow runner — executes recommended setup steps
# Usage: .\scripts\run_workflow.ps1

param(
    [string]$HfUsername = "",
    [switch]$SkipTraining,
    [switch]$StartServers
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root "backend\.venv\Scripts\python.exe"

Write-Host "`n=== Code Review Assistant — Workflow ===" -ForegroundColor Cyan

# Step 1: Prepare data
Write-Host "`n[1/5] Preparing training data..." -ForegroundColor Yellow
if (-not (Test-Path "$Root\data\train.jsonl")) {
    & $Python "$Root\scripts\prepare_data.py" --max-samples 5000 --output "$Root\data\train.jsonl"
} else {
    $lines = (Get-Content "$Root\data\train.jsonl" | Measure-Object -Line).Lines
    Write-Host "  Ready: $lines training examples in data/train.jsonl" -ForegroundColor Green
}

# Step 2: Fine-tune guidance
Write-Host "`n[2/5] Fine-tuning (Colab recommended — free T4 GPU)..." -ForegroundColor Yellow
if ($SkipTraining) {
    Write-Host "  Skipped" -ForegroundColor Gray
} else {
    Write-Host "  RECOMMENDED: Open notebooks/finetune_codereviewer_lora.ipynb in Google Colab" -ForegroundColor Cyan
    Write-Host "    1. Runtime -> Change runtime type -> T4 GPU" -ForegroundColor White
    Write-Host "    2. Set HF_TOKEN + HF_USERNAME in cell 2" -ForegroundColor White
    Write-Host "    3. Run all cells (~2-4 hours)" -ForegroundColor White
    Write-Host "  Alternative (paid): hf auth login && hf jobs uv run --flavor t4-medium --detach --secrets HF_TOKEN -e HF_USERNAME=you scripts/train_hf.py" -ForegroundColor Gray
}

# Step 3: Configure .env
Write-Host "`n[3/5] Configuring .env..." -ForegroundColor Yellow
$username = if ($HfUsername) { $HfUsername } else { "your-username" }
@"
INFERENCE_MODE=demo
HF_TOKEN=
BASE_MODEL_ID=mistralai/Mistral-7B-Instruct-v0.3
FINETUNED_MODEL_ID=$username/code-review-mistral-lora
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
"@ | Set-Content "$Root\.env" -Encoding UTF8
Write-Host "  .env updated (demo mode until Colab training finishes)" -ForegroundColor Green

# Step 4: Evaluate
Write-Host "`n[4/5] Running BLEU evaluation..." -ForegroundColor Yellow
& $Python "$Root\evaluation\evaluate.py" --samples 100 --mode demo

# Step 5: Servers
Write-Host "`n[5/5] Starting app..." -ForegroundColor Yellow
if ($StartServers) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; .\.venv\Scripts\uvicorn main:app --reload --port 8000"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\frontend'; npm run dev"
    Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Green
    Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host "  Start manually:" -ForegroundColor Cyan
    Write-Host "    cd backend; .\.venv\Scripts\uvicorn main:app --reload --port 8000"
    Write-Host "    cd frontend; npm run dev"
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
