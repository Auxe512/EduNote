"""EduNote per-student notebook scoping.

Notebooks carry an `owner` (student id). The list endpoint must only return a
given student's notebooks when `owner` is supplied, so students never see each
other's notebooks. Runs against the real SurrealDB (like the other *_routes
tests) and cleans up the rows it creates.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from api.main import app


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_notebooks_are_scoped_by_owner():
    async with _client() as client:
        a = await client.post(
            "/api/notebooks",
            json={"name": "Scope A NB", "description": "", "owner": "user:scope_a"},
        )
        b = await client.post(
            "/api/notebooks",
            json={"name": "Scope B NB", "description": "", "owner": "user:scope_b"},
        )
        assert a.status_code == 200, a.text
        assert b.status_code == 200, b.text
        a_id, b_id = a.json()["id"], b.json()["id"]

        try:
            list_a = await client.get("/api/notebooks", params={"owner": "user:scope_a"})
            assert list_a.status_code == 200
            names_a = {nb["name"] for nb in list_a.json()}
            assert "Scope A NB" in names_a
            assert "Scope B NB" not in names_a  # B's notebook must not leak to A

            # Without an owner, the original behaviour (return all) is preserved.
            list_all = await client.get("/api/notebooks")
            all_names = {nb["name"] for nb in list_all.json()}
            assert {"Scope A NB", "Scope B NB"} <= all_names
        finally:
            await client.delete(f"/api/notebooks/{a_id}")
            await client.delete(f"/api/notebooks/{b_id}")
