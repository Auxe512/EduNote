import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from open_notebook.services.groq_service import GroqService

def test_parse_json_response():
    svc = GroqService.__new__(GroqService)
    raw = '```json\n[{"topic": "Pipeline", "count": 5}]\n```'
    result = svc._parse_json(raw)
    assert result == [{"topic": "Pipeline", "count": 5}]

def test_parse_json_no_fence():
    svc = GroqService.__new__(GroqService)
    raw = '[{"front": "Q", "back": "A"}]'
    result = svc._parse_json(raw)
    assert result[0]["front"] == "Q"

def test_groq_service_init():
    with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
        svc = GroqService()
        assert svc.model_name == "llama-3.1-8b-instant"
