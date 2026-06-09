import base64
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI

from config import get_openai_vision_config
from llm.utils import extract_json

SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

VISION_SYSTEM_PROMPT = """\
Ты эксперт по распознаванию продуктов на фотографиях из домашней кухни и магазина.
По фотографии определи только съедобные продукты и ингредиенты.

Внимательно анализируй:
- продукты в сетках и мешках (картофель, лук, цитрусы и т.д.);
- продукты в прозрачных пакетах и плёнке;
- продукты в картонной и пластиковой упаковке;
- надписи, этикетки и логотипы на упаковке (рыба, мясо, молочные продукты);
- овощи похожей формы и цвета — не путай морковь с колбасой, \
огурец с кабачком, помидор с яблоком и т.п.

Правила уверенности:
- В "ingredients" добавляй только те продукты, в которых ты уверен.
- Если продукт виден, но распознан неуверенно — НЕ угадывай и НЕ заменяй \
случайным похожим продуктом. Добавь в "uncertain_ingredients" с кратким пояснением \
в скобках, например: "картофель (в сетке, виден частично)" или "минтай (упаковка, \
надпись нечитаема)".
- Не добавляй продукты, которых нет на фото.
- Не дублируй один продукт в обоих списках.

Названия — на русском, в именительном падеже (помидор, огурец, картофель, минтай).
Не включай посуду, мебель и непищевые предметы.

Ответ верни ТОЛЬКО валидным JSON без markdown.
"""

VISION_USER_PROMPT = """\
Внимательно изучи изображение и перечисли все видимые продукты.

Особое внимание:
1. Сетки и мешки с овощами — определи содержимое по форме и цвету сквозь упаковку.
2. Прозрачные пакеты — что внутри.
3. Упаковки с этикеткой — прочитай название продукта, если текст виден.
4. Похожие по цвету овощи — не путай морковь с колбасой, лук с чесноком в упаковке и т.д.
5. Если сомневаешься — не заменяй продукт другим, укажи в uncertain_ingredients.

Верни JSON строго в формате:
{
  "ingredients": ["уверенно распознанные продукты"],
  "uncertain_ingredients": ["продукты под сомнением"]
}
"""


@dataclass
class VisionDetectionResult:
    """ingredients — уверенные продукты; uncertain_ingredients — требуют подтверждения в CLI."""

    ingredients: list[str]
    uncertain_ingredients: list[str]
    processing_time: float


def _normalize_ingredient_list(raw_value: Any) -> list[str]:
    if not raw_value:
        return []

    if isinstance(raw_value, str):
        raw_value = [item.strip() for item in raw_value.split(",") if item.strip()]

    return [str(item).strip() for item in raw_value if str(item).strip()]


def _encode_image(image_path: Path) -> tuple[str, str]:
    suffix = image_path.suffix.lower()
    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_IMAGE_SUFFIXES))
        raise ValueError(
            f"Неподдерживаемый формат изображения: {suffix}. "
            f"Допустимы: {supported}"
        )

    mime_type = MIME_TYPES[suffix]
    image_data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    return mime_type, image_data


def detect_ingredients_from_image(image_path: Path) -> VisionDetectionResult:
    config = get_openai_vision_config()
    if not config["api_key"]:
        raise ValueError("OPENAI_API_KEY не задан в .env")

    if not image_path.is_file():
        raise FileNotFoundError(f"Файл изображения не найден: {image_path}")

    mime_type, image_data = _encode_image(image_path)
    client = OpenAI(api_key=config["api_key"])

    started_at = time.perf_counter()
    response = client.chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_USER_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    processing_time = time.perf_counter() - started_at

    content = response.choices[0].message.content or ""
    data = extract_json(content)
    ingredients = _normalize_ingredient_list(data.get("ingredients"))
    uncertain_ingredients = _normalize_ingredient_list(data.get("uncertain_ingredients"))

    if not ingredients and not uncertain_ingredients:
        raise ValueError("На изображении не удалось распознать ингредиенты.")

    return VisionDetectionResult(
        ingredients=ingredients,
        uncertain_ingredients=uncertain_ingredients,
        processing_time=processing_time,
    )
