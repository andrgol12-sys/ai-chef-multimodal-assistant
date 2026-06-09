import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
INPUT_DIR = PROJECT_ROOT / "inputs"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_IMAGES_DIR = OUTPUT_DIR / "images"


def ensure_inputs_dir() -> Path:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    return INPUT_DIR


def load_env() -> None:
    """Load environment variables from .env in the project root."""
    load_dotenv(PROJECT_ROOT / ".env")


def get_openai_config() -> dict[str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    return {"api_key": api_key, "model": model}


def get_openai_vision_config() -> dict[str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini").strip()
    return {"api_key": api_key, "model": model}


def get_openai_image_config() -> dict[str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3").strip()
    size = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024").strip()
    return {"api_key": api_key, "model": model, "size": size}


def ensure_output_images_dir() -> Path:
    OUTPUT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_IMAGES_DIR


def get_gigachat_config() -> dict[str, str]:
    credentials = os.getenv("GIGACHAT_CREDENTIALS", "").strip()
    model = os.getenv("GIGACHAT_MODEL", "GigaChat").strip()
    scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS").strip()
    verify_ssl = os.getenv("GIGACHAT_VERIFY_SSL", "false").strip().lower()
    return {
        "credentials": credentials,
        "model": model,
        "scope": scope,
        "verify_ssl": verify_ssl,
    }


def get_default_provider() -> str:
    return os.getenv("LLM_PROVIDER", "openai").strip().lower()
