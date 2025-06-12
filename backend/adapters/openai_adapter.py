# adapters/openai.py
from langchain_community.chat_models import ChatOpenAI
from base import LLMClientBase

class OpenAIAdapter(LLMClientBase):
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = ChatOpenAI(openai_api_key=api_key)

    async def generate(self, prompt: str) -> str:
        resp = await self.client.apredict(messages=[{"role":"user","content":prompt}])
        return resp.content
