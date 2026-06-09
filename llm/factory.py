from llm.base import LLMClient
from llm.gigachat_client import GigaChatClient
from llm.openai_client import OpenAIClient


def create_llm_client(provider: str) -> LLMClient:
    normalized = provider.strip().lower()
    if normalized == "openai":
        return OpenAIClient()
    if normalized == "gigachat":
        return GigaChatClient()
    raise ValueError(
        f"Неизвестный провайдер: {provider}. Используйте openai или gigachat."
    )
