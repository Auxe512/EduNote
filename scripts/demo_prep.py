"""Pre-cache all AI-generated content before Demo Day.

Quick Prep runs the slow Groq calls (exam analysis + quiz + flashcards) once and
stores the results, so that on Demo Day every student hits cached data instead of
the 6000 TPM free-tier limit all at once.

Usage:
    python scripts/demo_prep.py --notebook notebook:YOUR_ID [--source source:EXAM_PDF_ID]

Find the notebook id in the browser URL (/notebooks/<id>) and the exam source id
from the source panel. --source is optional; omit it if you have no past-exam PDF.
"""

import argparse
import asyncio
import sys

import httpx

API = "http://localhost:5055/api"


async def prep(notebook_id: str, exam_source_id: str | None) -> int:
    async with httpx.AsyncClient(timeout=180) as client:
        print(f"Notebook: {notebook_id}")
        print(f"Exam source: {exam_source_id or '(none — skipping exam analysis)'}")
        print("\nStep 1/2: Quick Prep (analyze exam + generate questions + flashcards)...")
        try:
            resp = await client.post(
                f"{API}/edunote/quickprep/{notebook_id}",
                json={"exam_source_id": exam_source_id},
            )
        except httpx.ConnectError:
            print(f"\n✗ Cannot reach the API at {API}.")
            print("  Make sure the backend is running (docker-compose up -d).")
            return 1

        if resp.status_code != 200:
            print(f"\n✗ Quick Prep failed (HTTP {resp.status_code}): {resp.text[:500]}")
            return 1

        results = resp.json()
        _report_section("Exam analysis", results.get("exam_analysis"))
        _report_section("Quiz", results.get("quiz"))
        _report_section("Flashcards", results.get("flashcards"))

        print("\nStep 2/2: Verifying cached content...")
        questions = await _count(client, f"{API}/edunote/quiz/questions/{notebook_id}")
        flashcards = await _count(client, f"{API}/edunote/flashcards/{notebook_id}")
        topics = await _count(client, f"{API}/edunote/exam/topics/{notebook_id}")

        print(f"  Exam topics cached: {topics}")
        print(f"  Questions cached:   {questions}")
        print(f"  Flashcards cached:  {flashcards}")

        if questions == 0 and flashcards == 0:
            print("\n✗ Nothing was cached. Check that the notebook has notes uploaded.")
            return 1

        print("\n✓ Done! Demo content is cached and ready.")
        return 0


def _report_section(label: str, payload) -> None:
    """Print a one-line status for each Quick Prep sub-result."""
    if not isinstance(payload, dict):
        print(f"  {label}: {payload}")
        return
    if "error" in payload:
        print(f"  {label}: ✗ {payload['error']}")
    elif "skipped" in payload:
        print(f"  {label}: skipped ({payload['skipped']})")
    else:
        generated = payload.get("generated")
        detail = f"generated {generated}" if generated is not None else "ok"
        print(f"  {label}: ✓ {detail}")


async def _count(client: httpx.AsyncClient, url: str) -> int:
    """Return the length of a list endpoint, or 0 on any failure."""
    try:
        resp = await client.get(url)
        data = resp.json()
        return len(data) if isinstance(data, list) else 0
    except (httpx.HTTPError, ValueError):
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-cache EduNote AI content for Demo Day.")
    parser.add_argument("--notebook", required=True, help="e.g. notebook:abc123")
    parser.add_argument("--source", default=None, help="past-exam source id, e.g. source:xyz789")
    args = parser.parse_args()
    sys.exit(asyncio.run(prep(args.notebook, args.source)))
