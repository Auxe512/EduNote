import os
import json
import re
from typing import Any, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


class GroqService:
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        self.model_name = model_name
        self._llm: Optional[ChatGroq] = None

    @property
    def llm(self) -> ChatGroq:
        # Lazily construct the client so importing this module (and the API) does
        # not crash when GROQ_API_KEY is unset — only actual use should fail.
        if self._llm is None:
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("GROQ_API_KEY is not set")
            # temperature=0 for deterministic, well-formed JSON output.
            self._llm = ChatGroq(model=self.model_name, api_key=api_key, temperature=0)
        return self._llm

    async def call(self, system: str, user: str) -> str:
        messages = [SystemMessage(content=system), HumanMessage(content=user)]
        response = await self.llm.ainvoke(messages)
        return response.content

    def _parse_json(self, raw: str) -> Any:
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: the model wrapped the JSON in prose. Extract the first
            # embedded array or object and parse that.
            match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            raise

    async def call_json(self, system: str, user: str) -> Any:
        raw = await self.call(system, user)
        return self._parse_json(raw)
