# backend/llm/vertexai_adapter.py
from langchain_google_vertexai import ChatVertexAI
from base import LLMClientBase

class VertexAIClient(LLMClientBase):
    def __init__(self, api_key: str):
        self._client = ChatVertexAI(api_key=api_key, model="chat-bison@001")
    async def generate(self, prompt: str) -> str:
        resp = await self._client.apredict(prompt)
        return resp.text
