import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from config import OUTPUT_DIR
from models import RecipeResult


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def build_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


_STEP_PREFIX_PATTERN = re.compile(
    r"^(?:шаг\s*\d+[\.\):\-]?\s*|\d+[\.\):\-]\s*)",
    re.IGNORECASE,
)


def strip_step_prefix(step: str) -> str:
    cleaned = step.strip()
    while True:
        match = _STEP_PREFIX_PATTERN.match(cleaned)
        if not match:
            break
        cleaned = cleaned[match.end() :].strip()
    return cleaned


def build_session_metadata(
    *,
    vision_detected: list[str] | None = None,
    vision_uncertain: list[str] | None = None,
    text_ingredients: list[str] | None = None,
    vision_image: str | None = None,
    vision_processing_time: float | None = None,
) -> dict[str, Any] | None:
    if not any(
        [
            vision_detected,
            vision_uncertain,
            text_ingredients,
            vision_image,
            vision_processing_time,
        ]
    ):
        return None

    metadata: dict[str, Any] = {}
    if vision_detected is not None:
        metadata["detected_ingredients"] = vision_detected
    if vision_uncertain is not None:
        metadata["uncertain_ingredients"] = vision_uncertain
    if text_ingredients is not None:
        metadata["text_ingredients"] = text_ingredients
    if vision_image is not None:
        metadata["image_path"] = vision_image
    if vision_processing_time is not None:
        metadata["processing_time_sec"] = round(vision_processing_time, 3)
    return metadata


def session_to_dict(
    result: RecipeResult,
    *,
    vision_detected: list[str] | None = None,
    vision_uncertain: list[str] | None = None,
    text_ingredients: list[str] | None = None,
    vision_image: str | None = None,
    vision_processing_time: float | None = None,
) -> dict[str, Any]:
    payload = recipe_to_dict(result)
    vision_meta = build_session_metadata(
        vision_detected=vision_detected,
        vision_uncertain=vision_uncertain,
        text_ingredients=text_ingredients,
        vision_image=vision_image,
        vision_processing_time=vision_processing_time,
    )
    if vision_meta:
        payload["vision"] = vision_meta
    return payload


def recipe_to_dict(result: RecipeResult) -> dict:
    return {
        "source_ingredients": result.source_ingredients,
        "dishes": [
            {
                "name": dish.name,
                "description": dish.description,
                "difficulty": dish.difficulty,
                "calories": dish.calories,
                "cooking_time": dish.cooking_time,
                "serving_suggestion": dish.serving_suggestion,
                "ingredients": dish.ingredients,
                "steps": dish.steps,
            }
            for dish in result.dishes
        ],
    }


def format_vision_section(
    *,
    vision_detected: list[str] | None = None,
    vision_uncertain: list[str] | None = None,
    text_ingredients: list[str] | None = None,
    vision_image: str | None = None,
    vision_processing_time: float | None = None,
) -> list[str]:
    lines: list[str] = []
    if not any(
        [
            vision_detected,
            vision_uncertain,
            text_ingredients,
            vision_image,
            vision_processing_time,
        ]
    ):
        return lines

    lines.extend(["Распознавание изображения (OpenAI Vision)", "-" * 40])
    if vision_image:
        lines.append(f"Файл: {vision_image}")
    if vision_detected:
        lines.append(f"Уверенно распознано: {', '.join(vision_detected)}")
    if vision_uncertain:
        lines.append(f"Под сомнением: {', '.join(vision_uncertain)}")
    if text_ingredients:
        lines.append(f"Из аргументов --ingredients: {', '.join(text_ingredients)}")
    if vision_processing_time is not None:
        lines.append(f"Время обработки Vision: {vision_processing_time:.3f} сек")
    lines.append("")
    return lines


def format_recipe_text(
    result: RecipeResult,
    *,
    vision_detected: list[str] | None = None,
    vision_uncertain: list[str] | None = None,
    text_ingredients: list[str] | None = None,
    vision_image: str | None = None,
    vision_processing_time: float | None = None,
) -> str:
    lines = ["AI Chef — предложенные блюда", "=" * 40, ""]
    lines.extend(
        format_vision_section(
            vision_detected=vision_detected,
            vision_uncertain=vision_uncertain,
            text_ingredients=text_ingredients,
            vision_image=vision_image,
            vision_processing_time=vision_processing_time,
        )
    )
    lines.extend(
        [
            f"Итоговые ингредиенты: {', '.join(result.source_ingredients)}",
            "",
        ]
    )

    for index, dish in enumerate(result.dishes, start=1):
        lines.extend(
            [
                f"{index}. {dish.name}",
                "-" * 40,
                f"Описание: {dish.description}",
                f"Сложность: {dish.difficulty}",
                f"Калорийность: {dish.calories}",
                f"Время приготовления: {dish.cooking_time}",
                f"Подача: {dish.serving_suggestion}",
                "",
                "Ингредиенты:",
            ]
        )
        lines.extend(f"  - {item}" for item in dish.ingredients)
        lines.append("")
        lines.append("Рецепт:")
        lines.extend(
            f"  {step_index}. {strip_step_prefix(step)}"
            for step_index, step in enumerate(dish.steps, start=1)
        )
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def save_recipe(
    result: RecipeResult,
    output_format: str,
    *,
    vision_detected: list[str] | None = None,
    vision_uncertain: list[str] | None = None,
    text_ingredients: list[str] | None = None,
    vision_image: str | None = None,
    vision_processing_time: float | None = None,
) -> list[Path]:
    output_dir = ensure_output_dir()
    timestamp = build_timestamp()
    saved_files: list[Path] = []

    normalized = output_format.strip().lower()
    if normalized in {"txt", "both"}:
        txt_path = output_dir / f"recipes_{timestamp}.txt"
        txt_path.write_text(
            format_recipe_text(
                result,
                vision_detected=vision_detected,
                vision_uncertain=vision_uncertain,
                text_ingredients=text_ingredients,
                vision_image=vision_image,
                vision_processing_time=vision_processing_time,
            ),
            encoding="utf-8",
        )
        saved_files.append(txt_path)

    if normalized in {"json", "both"}:
        json_path = output_dir / f"recipes_{timestamp}.json"
        json_path.write_text(
            json.dumps(
                session_to_dict(
                    result,
                    vision_detected=vision_detected,
                    vision_uncertain=vision_uncertain,
                    text_ingredients=text_ingredients,
                    vision_image=vision_image,
                    vision_processing_time=vision_processing_time,
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        saved_files.append(json_path)

    if not saved_files:
        raise ValueError("Формат вывода должен быть txt, json или both.")

    return saved_files
