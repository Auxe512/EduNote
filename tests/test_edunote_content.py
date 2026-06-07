"""Tests for gathering a notebook's study text.

Quiz/flashcard generation must read BOTH notes (linked via `artifact`) and
uploaded sources (linked via `reference`), so that uploading lecture files is
enough to generate from — without manually creating notes.

DB-backed (same pattern as the other route tests).
"""

import uuid

import pytest

from api.edunote.content import gather_notebook_text
from open_notebook.database.repository import repo_query


@pytest.mark.asyncio
async def test_gather_includes_uploaded_source_text():
    """A notebook with only an uploaded source (no notes) still yields text."""
    nb = f"notebook:{uuid.uuid4().hex}"
    await repo_query(
        "CREATE type::thing($nb) SET name='t', description=''", {"nb": nb}
    )
    src = await repo_query(
        "CREATE source SET title='lecture', full_text=$ft",
        {"ft": "CPU pipeline has five stages: IF ID EX MEM WB."},
    )
    sid = str(src[0]["id"])
    await repo_query(f"RELATE {sid}->reference->{nb}")

    try:
        text = await gather_notebook_text(nb)
        assert "pipeline" in text.lower()
    finally:
        await repo_query("DELETE reference WHERE out=type::thing($nb)", {"nb": nb})
        await repo_query("DELETE source WHERE id=type::thing($s)", {"s": sid})
        await repo_query("DELETE type::thing($nb)", {"nb": nb})


@pytest.mark.asyncio
async def test_gather_includes_note_text():
    """A notebook with a note (artifact) still yields text (existing behaviour)."""
    nb = f"notebook:{uuid.uuid4().hex}"
    await repo_query(
        "CREATE type::thing($nb) SET name='t', description=''", {"nb": nb}
    )
    note = await repo_query(
        "CREATE note SET title='n', content=$c", {"c": "Normalization avoids anomalies."}
    )
    nid = str(note[0]["id"])
    await repo_query(f"RELATE {nid}->artifact->{nb}")

    try:
        text = await gather_notebook_text(nb)
        assert "normalization" in text.lower()
    finally:
        await repo_query("DELETE artifact WHERE out=type::thing($nb)", {"nb": nb})
        await repo_query("DELETE note WHERE id=type::thing($n)", {"n": nid})
        await repo_query("DELETE type::thing($nb)", {"nb": nb})


@pytest.mark.asyncio
async def test_gather_empty_notebook_returns_blank():
    nb = f"notebook:{uuid.uuid4().hex}"
    text = await gather_notebook_text(nb)
    assert text == ""
