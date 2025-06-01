import os
from pathlib import Path

MODEL: str = os.environ.get("PROPAGATE_MODEL")
PDF_DIR: Path = Path(os.environ.get("PROPAGATE_PDF_DIR"))
SUMMARIES_DIR: Path = Path(os.environ.get("PROPAGATE_SUMMARIES_DIR"))
CLAUDE_API_KEY: str | None = os.environ.get("PROPAGATE_ANTHROPIC_API_KEY")
MAX_SUMMARY_LENGTH: int = 250
MAX_TOKENS: int = 16000
