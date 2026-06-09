from dataclasses import dataclass, field
from typing import Any


@dataclass
class Dish:
    name: str
    description: str
    ingredients: list[str]
    steps: list[str]
    cooking_time: str
    difficulty: str
    calories: str
    serving_suggestion: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Dish":
        ingredients = data.get("ingredients") or []
        steps = data.get("steps") or data.get("recipe") or []

        if isinstance(ingredients, str):
            ingredients = [item.strip() for item in ingredients.split(",") if item.strip()]
        if isinstance(steps, str):
            steps = [line.strip() for line in steps.split("\n") if line.strip()]

        return cls(
            name=str(data.get("name", "Без названия")).strip(),
            description=str(data.get("description", "")).strip(),
            ingredients=[str(item).strip() for item in ingredients if str(item).strip()],
            steps=[str(item).strip() for item in steps if str(item).strip()],
            cooking_time=str(
                data.get("cooking_time") or data.get("time") or "не указано"
            ).strip(),
            difficulty=str(
                data.get("difficulty") or data.get("complexity") or "средний"
            ).strip(),
            calories=str(
                data.get("calories") or data.get("caloric_value") or "не указано"
            ).strip(),
            serving_suggestion=str(
                data.get("serving_suggestion")
                or data.get("serving")
                or data.get("presentation")
                or "не указано"
            ).strip(),
        )


@dataclass
class RecipeResult:
    source_ingredients: list[str]
    dishes: list[Dish] = field(default_factory=list)

    @classmethod
    def from_dict(cls, source_ingredients: list[str], data: dict[str, Any]) -> "RecipeResult":
        raw_dishes = data.get("dishes") or data.get("recipes") or []
        dishes = [Dish.from_dict(item) for item in raw_dishes if isinstance(item, dict)]
        return cls(source_ingredients=source_ingredients, dishes=dishes)
