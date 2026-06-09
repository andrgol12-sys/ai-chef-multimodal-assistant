import os
from pathlib import Path

from flask import Flask, abort, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

from config import INPUT_DIR, OUTPUT_DIR, ensure_inputs_dir, get_default_provider, load_env
from llm.factory import create_llm_client
from llm.openai_image import generate_dish_image
from llm.openai_vision import detect_ingredients_from_image
from main import merge_ingredients, normalize_ingredients
from output import save_recipe, strip_step_prefix

load_env()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ai-chef-dev-secret")

ALLOWED_UPLOAD_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
}


def parse_text_ingredients(raw_text: str) -> list[str]:
    if not raw_text.strip():
        return []

    items = []

    for chunk in raw_text.replace("\n", ",").split(","):
        chunk = chunk.strip()

        if chunk:
            items.append(chunk)

    return normalize_ingredients(items)


def save_uploaded_image(file_storage) -> Path | None:
    if not file_storage or not file_storage.filename:
        return None

    suffix = Path(file_storage.filename).suffix.lower()

    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError(
            f"Неподдерживаемый формат изображения: {suffix}. "
            f"Допустимы: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}"
        )

    ensure_inputs_dir()

    filename = secure_filename(file_storage.filename)

    if not filename:
        filename = f"upload{suffix}"

    image_path = INPUT_DIR / filename

    file_storage.save(image_path)

    return image_path.resolve()


def dish_to_template(dish) -> dict:
    return {
        "name": dish.name,
        "description": dish.description,
        "difficulty": dish.difficulty,
        "calories": dish.calories,
        "cooking_time": dish.cooking_time,
        "serving_suggestion": dish.serving_suggestion,
        "ingredients": dish.ingredients,
        "steps": [
            strip_step_prefix(step)
            for step in dish.steps
        ],
    }


def output_file_url(path: Path) -> str:
    relative = path.relative_to(OUTPUT_DIR)

    return url_for(
        "serve_output",
        filepath=str(relative).replace("\\", "/"),
    )


@app.route("/outputs/<path:filepath>")
def serve_output(filepath: str):

    file_path = (OUTPUT_DIR / filepath).resolve()
    output_root = OUTPUT_DIR.resolve()

    if (
        not str(file_path).startswith(str(output_root))
        or not file_path.is_file()
    ):
        abort(404)

    return send_from_directory(
        file_path.parent,
        file_path.name,
    )


@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "GET":
        return render_template(
            "index.html",
            default_provider=get_default_provider(),
        )

    statuses = []
    error = None

    ingredients_text = request.form.get("ingredients", "")
    provider = request.form.get("provider") or get_default_provider()

    use_uncertain = (
        request.form.get("use_uncertain")
        == "on"
    )

    uploaded_file = request.files.get("photo")

    vision_detected = []
    vision_uncertain = []
    vision_uncertain_included = []

    text_ingredients = []

    vision_image = None
    vision_processing_time = None

    saved_files = []

    dish_image_path = None
    dish_image_error = None

    dishes = []

    final_ingredients = []

    try:

        text_ingredients = parse_text_ingredients(
            ingredients_text
        )

        if uploaded_file and uploaded_file.filename:

            statuses.append({
                "label": "Распознаю продукты…",
                "done": False,
            })

            image_path = save_uploaded_image(
                uploaded_file
            )

            if image_path is None:
                raise ValueError(
                    "Не удалось сохранить изображение."
                )

            vision_image = str(image_path)

            vision_result = (
                detect_ingredients_from_image(
                    image_path
                )
            )

            vision_detected = (
                vision_result.ingredients
            )

            vision_uncertain = (
                vision_result.uncertain_ingredients
            )

            vision_processing_time = (
                vision_result.processing_time
            )

            statuses[-1]["done"] = True

        if use_uncertain and vision_uncertain:
            vision_uncertain_included = (
                vision_uncertain
            )

        final_ingredients = merge_ingredients(
            vision_detected,
            text_ingredients,
            vision_uncertain_included,
        )

        if not final_ingredients:
            raise ValueError(
                "Укажите ингредиенты текстом или загрузите фото."
            )

        statuses.append({
            "label": "Генерирую рецепты…",
            "done": False,
        })

        client = create_llm_client(
            provider
        )

        result = client.suggest_dishes(
            final_ingredients
        )

        dishes = [
            dish_to_template(dish)
            for dish in result.dishes
        ]

        statuses[-1]["done"] = True

        saved_files = save_recipe(
            result,
            "both",
            vision_detected=vision_detected or None,
            vision_uncertain=vision_uncertain or None,
            text_ingredients=text_ingredients or None,
            vision_image=vision_image,
            vision_processing_time=vision_processing_time,
        )

        if result.dishes:

            statuses.append({
                "label": "Создаю изображение блюда…",
                "done": False,
            })

            image_path, dish_image_error = (
                generate_dish_image(
                    result.dishes[0]
                )
            )

            if image_path:
                dish_image_path = (
                    output_file_url(
                        image_path
                    )
                )

            statuses[-1]["done"] = True

    except Exception as exc:

        error = str(exc)

        if statuses:
            statuses[-1]["done"] = False

    return render_template(
        "index.html",

        default_provider=provider,

        ingredients_text=ingredients_text,

        use_uncertain=use_uncertain,

        error=error,

        statuses=statuses,

        vision_detected=vision_detected,

        vision_uncertain=vision_uncertain,

        vision_uncertain_included=vision_uncertain_included,

        text_ingredients=text_ingredients,

        final_ingredients=final_ingredients,

        vision_processing_time=vision_processing_time,

        dishes=dishes,

        dish_image_path=dish_image_path,

        dish_image_error=dish_image_error,

        saved_files=[
            {
                "name": path.name,
                "url": output_file_url(path),
            }
            for path in saved_files
        ],
    )


if __name__ == "__main__":

    ensure_inputs_dir()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000,
    )