import sys
from pathlib import Path

# Vercel serverless entry — demo mode (no GPU deps)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from mangum import Mangum
from main import app

handler = Mangum(app, lifespan="off")
