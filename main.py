import argparse
import sys
from pathlib import Path

from config import INPUT_DIR, ensure_inputs_dir, get_default_provider, load_env
from llm.factory import create_llm_client
from llm.openai_image import format_saved_image_message, generate_dish_image
from llm.openai_vision import detect_ingredients_from_image
from output import format_recipe_text, save_recipe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Chef — подбор рецептов по списку ингредиентов."
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "gigachat"],
        default=None,
        help="LLM-провайдер (по умолчанию из LLM_PROVIDER в .env).",
    )
    parser.add_argument(
        "--format",
        choices=["txt", "json", "both"],
        default="both",
        help="Формат сохранения результата.",
    )
    parser.add_argument(
        "--ingredients",
        nargs="+",
        help="Список ингредиентов через пробел. Если не указан — интерактивный ввод.",
    )
    parser.add_argument(
        "--image",
        help="Путь к изображению продуктов для распознавания через OpenAI Vision.",
    )
    return parser.parse_args()


def read_ingredients_interactive() -> list[str]:
    print("AI Chef")
    print("Введите ингредиенты через запятую или по одному на строку.")
    print("Пустая строка завершит ввод.\n")

    ingredients: list[str] = []
    while True:
        try:
            line = input("Ингредиенты> ").strip()
        except EOFError:
            break

        if not line:
            break

        if "," in line:
            parts = [item.strip() for item in line.split(",") if item.strip()]
            ingredients.extend(parts)
        else:
            ingredients.append(line)

    return ingredients


def normalize_ingredients(raw_ingredients: list[str]) -> list[str]:
    normalized: list[str] = []
    for item in raw_ingredients:
        if "," in item:
            normalized.extend(part.strip() for part in item.split(",") if part.strip())
        elif item.strip():
            normalized.append(item.strip())
    return normalized


def merge_ingredients(*ingredient_lists: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for items in ingredient_lists:
        for item in items:
            key = item.strip().lower()
            if key and key not in seen:
                seen.add(key)
                merged.append(item.strip())

    return merged


def prompt_include_uncertain_ingredients(uncertain: list[str]) -> list[str]:
    if not uncertain:
        return []

    print("\nПод сомнением:")
    for index, item in enumerate(uncertain, start=1):
        print(f"{index}. {item}")

    while True:
        try:
            answer = input("\nИспользовать сомнительные продукты? (y/n): ").strip().lower()
        except EOFError:
            answer = "n"

        if answer in {"y", "yes", "д", "да"}:
            return uncertain
        if answer in {"n", "no", "н", "нет"}:
            return []
        print("Введите y или n.")


def resolve_image_path(image_arg: str) -> Path:
    ensure_inputs_dir()
    path = Path(image_arg)

    if path.is_file():
        return path.resolve()

    candidate = INPUT_DIR / image_arg
    if candidate.is_file():
        return candidate.resolve()

    raise FileNotFoundError(
        f"Изображение не найдено: {image_arg}. "
        f"Проверьте путь или положите файл в папку {INPUT_DIR.name}/"
    )


def collect_ingredients(args: argparse.Namespace) -> tuple[list[str], dict]:
    vision_detected: list[str] = []
    vision_uncertain: list[str] = []
    text_ingredients: list[str] = []
    vision_image: str | None = None
    vision_processing_time: float | None = None

    if args.image:
        image_path = resolve_image_path(args.image)
        vision_image = str(image_path)
        print(f"Распознаю продукты на изображении: {image_path.name}...")
        try:
            vision_result = detect_ingredients_from_image(image_path)
        except Exception as error:
            raise RuntimeError(f"Ошибка OpenAI Vision: {error}") from error

        vision_detected = vision_result.ingredients
        vision_uncertain = vision_result.uncertain_ingredients
        vision_processing_time = vision_result.processing_time

        print(f"Время обработки Vision: {vision_processing_time:.3f} сек")
        if vision_detected:
            print(f"Уверенно распознано: {', '.join(vision_detected)}")

    if args.ingredients:
        text_ingredients = normalize_ingredients(args.ingredients)
    elif not args.image:
        text_ingredients = read_ingredients_interactive()

    uncertain_included = prompt_include_uncertain_ingredients(vision_uncertain)

    ingredients = merge_ingredients(
        vision_detected,
        text_ingredients,
        uncertain_included,
    )
    session_meta = {
        "vision_detected": vision_detected or None,
        "vision_uncertain": vision_uncertain or None,
        "vision_uncertain_included": uncertain_included or None,
        "text_ingredients": text_ingredients or None,
        "vision_image": vision_image,
        "vision_processing_time": vision_processing_time,
    }
    return ingredients, session_meta


def main() -> int:
    load_env()
    ensure_inputs_dir()
    args = parse_args()

    try:
        ingredients, session_meta = collect_ingredients(args)
    except Exception as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1

    if not ingredients:
        print("Ошибка: список ингредиентов пуст.", file=sys.stderr)
        return 1

    provider = args.provider or get_default_provider()

    try:
        client = create_llm_client(provider)
        print(f"Запрашиваю рецепты у {provider}...\n")
        result = client.suggest_dishes(ingredients)
    except Exception as error:
        print(f"Ошибка при обращении к LLM: {error}", file=sys.stderr)
        return 1

    print(
        format_recipe_text(
            result,
            vision_detected=session_meta["vision_detected"],
            vision_uncertain=session_meta["vision_uncertain"],
            text_ingredients=session_meta["text_ingredients"],
            vision_image=session_meta["vision_image"],
            vision_processing_time=session_meta["vision_processing_time"],
        )
    )

    try:
        saved_files = save_recipe(
            result,
            args.format,
            vision_detected=session_meta["vision_detected"],
            vision_uncertain=session_meta["vision_uncertain"],
            text_ingredients=session_meta["text_ingredients"],
            vision_image=session_meta["vision_image"],
            vision_processing_time=session_meta["vision_processing_time"],
        )
    except Exception as error:
        print(f"Ошибка при сохранении результата: {error}", file=sys.stderr)
        return 1

    print("Результат сохранён:")
    for path in saved_files:
        print(f"  - {path}")

    if result.dishes:
        image_path, image_error = generate_dish_image(result.dishes[0])
        if image_path:
            print(f"\nИзображение блюда сохранено:\n{format_saved_image_message(image_path)}")
        else:
            print(
                f"\nПредупреждение: не удалось сгенерировать изображение блюда. {image_error}",
                file=sys.stderr,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
