from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

from config import get_gigachat_config
from llm.base import LLMClient
from llm.utils import parse_recipe_response
from models import RecipeResult
from prompts import SYSTEM_PROMPT, build_user_prompt


class GigaChatClient(LLMClient):
    def __init__(self) -> None:
        config = get_gigachat_config()
        if not config["credentials"]:
            raise ValueError("GIGACHAT_CREDENTIALS не задан в .env")

        verify_ssl = config["verify_ssl"] in {"1", "true", "yes"}
        self._model = config["model"]
        self._client = GigaChat(
            credentials=config["credentials"],
            scope=config["scope"],
            model=self._model,
            verify_ssl_certs=verify_ssl,
        )

    def suggest_dishes(self, ingredients: list[str]) -> RecipeResult:
        payload = Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content=SYSTEM_PROMPT),
                Messages(
                    role=MessagesRole.USER,
                    content=build_user_prompt(ingredients),
                ),
            ],
            temperature=0.85,
        )
        response = self._client.chat(payload)
        content = response.choices[0].message.content or ""
        return parse_recipe_response(ingredients, content)
