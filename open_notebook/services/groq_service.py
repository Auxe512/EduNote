import os
import json
import re
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


class GroqService:
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        self.model_name = model_name
        self.llm = ChatGroq(
            model=model_name,
            api_key=os.environ["GROQ_API_KEY"],
            temperature=0.7,
        )

    async def call(self, system: str, user: str) -> str:
        messages = [SystemMessage(content=system), HumanMessage(content=user)]
        response = await self.llm.ainvoke(messages)
        return response.content

    def _parse_json(self, raw: str) -> Any:
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        return json.loads(cleaned)

    async def call_json(self, system: str, user: str) -> Any:
        raw = await self.call(system, user)
        return self._parse_json(raw)
