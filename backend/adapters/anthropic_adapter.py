import os
import httpx
from typing import Dict, List, Optional, Any, Union
from langchain_anthropic import ChatAnthropic
from base import LLMClientBase

class AnthropicClient(LLMClientBase):
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
        self._client = ChatAnthropic(
            anthropic_api_key=api_key,
            model_name=model
        )

    async def upload_file(self, file_path: str, purpose: str = "assistant") -> Dict[str, Any]:
        """Upload a file to Anthropic's storage."""
        url = f"{self.base_url}/files"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "files-api-2025-04-14"
        }
        
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    files=files,
                    data={"purpose": purpose}
                )
                response.raise_for_status()
                return response.json()

    async def chat_with_file(
        self,
        messages: List[Dict[str, Any]],
        file_id: str,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> str:
        """Send a chat message with a file reference to Anthropic."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "files-api-2025-04-14",
            "content-type": "application/json"
        }
        
        # Add file reference to the last user message
        if messages and messages[-1]["role"] == "user":
            if isinstance(messages[-1]["content"], str):
                messages[-1]["content"] = [
                    {"type": "text", "text": messages[-1]["content"]},
                    {
                        "type": "document",
                        "source": {
                            "type": "file",
                            "file_id": file_id
                        }
                    }
                ]
            elif isinstance(messages[-1]["content"], list):
                messages[-1]["content"].append({
                    "type": "document",
                    "source": {
                        "type": "file",
                        "file_id": file_id
                    }
                })
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        url = f"{self.base_url}/messages"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        response = await self._client.agenerate([prompt])
        return response.generations[0][0].text
