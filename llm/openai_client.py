from openai import OpenAI

from config import get_openai_config
from llm.base import LLMClient
from llm.utils import parse_recipe_response
from models import RecipeResult
from prompts import SYSTEM_PROMPT, build_user_prompt


class OpenAIClient(LLMClient):
    def __init__(self) -> None:
        config = get_openai_config()
        if not config["api_key"]:
            raise ValueError("OPENAI_API_KEY не задан в .env")

        self._client = OpenAI(api_key=config["api_key"])
        self._model = config["model"]

    def suggest_dishes(self, ingredients: list[str]) -> RecipeResult:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(ingredients)},
            ],
            temperature=0.85,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        return parse_recipe_response(ingredients, content)
