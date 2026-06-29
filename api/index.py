import os
import sys
from pathlib import Path

# Vercel FastAPI entrypoint — exports `app` (not Mangum handler)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
os.environ.setdefault("INFERENCE_MODE", "demo")

from main import app  # noqa: E402, F401
