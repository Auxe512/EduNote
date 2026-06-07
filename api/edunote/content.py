"""Shared helper for collecting a notebook's study text.

EduNote generation (quiz, flashcards) reads from BOTH:
- notes linked via the `artifact` relation (note -> notebook), and
- sources linked via the `reference` relation (source -> notebook).

Uploaded lecture files become `source` records, so reading sources is what makes
"upload a lecture, then one-click prep" actually work.
"""

from open_notebook.database.repository import repo_query

# Groq free tier: 6000 TPM. ~4000 chars keeps mixed Chinese/English under the limit.
DEFAULT_LIMIT_CHARS = 4000


async def gather_notebook_text(notebook_id: str, limit_chars: int = DEFAULT_LIMIT_CHARS) -> str:
    """Return the combined text of a notebook's notes and uploaded sources,
    truncated to ``limit_chars``."""
    note_rows = await repo_query(
        "SELECT note.content AS content FROM "
        "(SELECT in AS note FROM artifact WHERE out=type::thing($nb) FETCH note)",
        {"nb": notebook_id},
    )
    source_rows = await repo_query(
        "SELECT full_text AS content FROM source "
        "WHERE id IN (SELECT VALUE in FROM reference WHERE out=type::thing($nb))",
        {"nb": notebook_id},
    )

    parts = [
        r.get("content", "")
        for r in (note_rows or []) + (source_rows or [])
        if r.get("content")
    ]
    return "\n\n".join(parts)[:limit_chars]
