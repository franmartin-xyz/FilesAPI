# factory.py
from adapters.openai_adapter import OpenAIAdapter
from adapters.anthropic_adapter import AnthropicClient 
from adapters.vertexai_adapter import VertexAIClient

_MAP = {
  "openai": OpenAIAdapter,
  "anthropic": AnthropicClient,
  "vertexai": VertexAIClient,
}

def get_llm_client(provider: str, api_key: str):
    cls = _MAP.get(provider.lower())
    if not cls:
        raise ValueError(f"Unsupported provider: {provider}")
    return cls(api_key)
