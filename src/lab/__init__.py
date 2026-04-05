"""OpenHands Lab - A local-first orchestration layer for the OpenHands SDK."""

from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
_project_root = Path(__file__).parent.parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    # Also try current working directory
    load_dotenv()

__version__ = "0.1.0"
