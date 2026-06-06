import pytest
import os

@pytest.fixture
def auth_headers():
    password = os.environ.get("NOTEBOOK_PASSWORD", "test-password")
    return {"Authorization": f"Bearer {password}"}
