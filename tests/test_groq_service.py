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

def test_parse_json_extracts_array_from_surrounding_prose():
    """Llama sometimes adds prose around the JSON; we should still recover the array."""
    svc = GroqService.__new__(GroqService)
    raw = 'Sure! Here are the topics:\n[{"topic": "Cache", "count": 3}]\nHope this helps.'
    result = svc._parse_json(raw)
    assert result == [{"topic": "Cache", "count": 3}]


def test_groq_service_init():
    with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
        svc = GroqService()
        assert svc.model_name == "llama-3.1-8b-instant"


def test_init_does_not_require_api_key_until_called():
    """Constructing the service (which happens at module import) must not crash
    the whole API when GROQ_API_KEY is unset — only using it should error."""
    with patch.dict("os.environ", {}, clear=True):
        svc = GroqService()  # must not raise
        assert svc.model_name == "llama-3.1-8b-instant"
        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            _ = svc.llm
