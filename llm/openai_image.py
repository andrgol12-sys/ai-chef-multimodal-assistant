import base64
import re
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

from openai import OpenAI

from config import PROJECT_ROOT, ensure_output_images_dir, get_openai_image_config
from models import Dish


def build_dish_image_prompt(dish: Dish) -> str:
    parts = [
        f"Фотореалистичное аппетитное блюдо: {dish.name}.",
        dish.description,
        f"Подача: {dish.serving_suggestion}.",
        "Домашняя кухня, натуральное освещение, высокое качество, без текста на изображении.",
    ]
    return " ".join(part.strip() for part in parts if part.strip())


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
    cleaned = re.sub(r"[\s_-]+", "_", cleaned.strip().lower())
    return cleaned[:50] or "dish"


def _relative_output_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _save_image_bytes(image_bytes: bytes, dish: Dish) -> Path:
    output_dir = ensure_output_images_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{_safe_filename(dish.name)}_{timestamp}.png"
    image_path = output_dir / filename
    image_path.write_bytes(image_bytes)
    return image_path


def _download_image(url: str) -> bytes:
    with urlopen(url, timeout=60) as response:
        return response.read()


def generate_dish_image(dish: Dish) -> tuple[Path | None, str | None]:
    """Generate and save dish image. Returns (path, error_message)."""
    config = get_openai_image_config()
    if not config["api_key"]:
        return None, "OPENAI_API_KEY не задан в .env"

    prompt = build_dish_image_prompt(dish)
    client = OpenAI(api_key=config["api_key"])

    try:
        response = client.images.generate(
            model=config["model"],
            prompt=prompt,
            size=config["size"],
            n=1,
        )
    except Exception as error:
        return None, str(error)

    if not response.data:
        return None, "OpenAI Image API не вернул изображение."

    image_item = response.data[0]
    try:
        if image_item.b64_json:
            image_bytes = base64.b64decode(image_item.b64_json)
        elif image_item.url:
            image_bytes = _download_image(image_item.url)
        else:
            return None, "В ответе API отсутствуют данные изображения."
    except Exception as error:
        return None, f"Не удалось сохранить изображение: {error}"

    try:
        saved_path = _save_image_bytes(image_bytes, dish)
    except Exception as error:
        return None, str(error)

    return saved_path, None


def format_saved_image_message(image_path: Path) -> str:
    return _relative_output_path(image_path)
