import os
import json
from pathlib import Path

# Default keys file path (workspace-relative). Can be overridden by setting the API_KEYS_FILE env var.
DEFAULT_KEYS_PATH = Path(__file__).parent.parent / "secrets" / "api_keys.json"


def load_api_keys(file_path: str = None) -> dict:
    """Load API keys from a JSON file. Returns empty dict if file missing or invalid.

    Priority: explicit file_path arg -> API_KEYS_FILE env var -> DEFAULT_KEYS_PATH
    """
    path = None
    if file_path:
        path = Path(file_path)
    elif os.environ.get("API_KEYS_FILE"):
        path = Path(os.environ.get("API_KEYS_FILE"))
    else:
        path = DEFAULT_KEYS_PATH

    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


if __name__ == "__main__":
    print("API keys loader. Set API_KEYS_FILE to point to a JSON file with keys like {'GROQ_API_KEY': '...'}")
