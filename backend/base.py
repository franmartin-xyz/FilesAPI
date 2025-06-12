# backend/llm/base.py

import os
from abc import ABC, abstractmethod


class LLMClientBase(ABC):
    """
    Abstract base class for all LLM providers.
    """

    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        # allow passing api_key explicitly, otherwise fall back to env var
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError("LLM API key must be provided either via constructor or LLM_API_KEY env var")

        # allow passing in a model name, otherwise fall back to env var or adapter default
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME")

        # let adapter subclasses do any extra setup / validation
        self.validate()

    def validate(self) -> None:
        """
        Hook for adapters to verify that the environment / credentials are correct.
        E.g. ping a test endpoint, check that required client libs are installed, etc.
        """
        pass

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Send `prompt` to the underlying LLM and return its text output.

        Parameters
        ----------
        prompt : str
            The text prompt to send to the LLM.
        **kwargs
            Provider-specific overrides (e.g. temperature, max_tokens, etc).

        Returns
        -------
        str
            The generated text from the model.
        """
        ...
