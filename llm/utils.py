import json
import re
from typing import Any

from models import RecipeResult


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("Модель вернула ответ без JSON.") from None
        return json.loads(match.group(0))


def parse_recipe_response(ingredients: list[str], content: str) -> RecipeResult:
    data = extract_json(content)
    result = RecipeResult.from_dict(ingredients, data)
    if len(result.dishes) != 3:
        raise ValueError(
            f"Ожидалось 3 блюда, модель вернула {len(result.dishes)}."
        )
    return result
