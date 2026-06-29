# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "datasets",
#   "accelerate",
#   "trl",
#   "peft",
#   "bitsandbytes",
#   "transformers",
#   "huggingface_hub",
#   "torch",
# ]
# ///
"""HF Jobs entrypoint: hf jobs uv run --flavor t4-medium --detach --secrets HF_TOKEN -e HF_USERNAME=you scripts/train_hf.py"""

import runpy

runpy.run_path("scripts/train.py", run_name="__main__")
