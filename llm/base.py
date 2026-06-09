from abc import ABC, abstractmethod

from models import RecipeResult


class LLMClient(ABC):
    @abstractmethod
    def suggest_dishes(self, ingredients: list[str]) -> RecipeResult:
        raise NotImplementedError
