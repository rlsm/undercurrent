"""
Undercurrent — AI review layer

Takes every 'pending' event with no AI summary yet and asks Claude to:
  1. Write a short, editorial-voice summary (the kind that goes in the newsletter)
  2. Give a verdict: worth_it / skip / needs_review
  3. Give a one-line reasoning, shown to Ronald in the approval panel

This NEVER auto-publishes anything — it only prepares events for human review.
Run with: python ai_review.py

Requires: pip install anthropic --break-system-packages
Requires env var: ANTHROPIC_API_KEY
"""
import json
import os
from models import get_db, init_db

try:
    import anthropic
except ImportError:
    raise SystemExit(
        "Missing dependency. Run: pip install anthropic --break-system-packages"
    )

SYSTEM_PROMPT = """You are the editorial voice behind Undercurrent, a newsletter and \
membership site covering the electronic music scene in NJ/NY, with plans to expand \
nationally and eventually to Latin America. Your job is to evaluate raw event listings \
and help a human editor (Ronald, who knows the scene personally) decide what's worth \
covering.

Voice: dry, specific, a little dark-editorial — not hype-y, not full of exclamation \
points. You're talking to people who already know what a "banger" is and don't need \
to be told something is "unmissable." You earn trust by being honest when something \
is mid.

For each event you receive, respond ONLY with valid JSON in this exact shape, nothing \
else, no markdown fences:

{
  "summary": "2-3 sentences in the Undercurrent voice, suitable to paste into the \
newsletter. Mention what makes this specific event worth knowing about or skipping.",
  "verdict": "worth_it" | "skip" | "needs_review",
  "reasoning": "one short sentence explaining the verdict, for the editor's eyes only"
}

Use "needs_review" when you genuinely don't have enough signal (e.g. an unknown small \
local artist with no other context) — don't force a worth_it/skip call you can't \
support."""


def build_user_prompt(event):
    lineup = json.loads(event["lineup"]) if event["lineup"] else []
    genres = json.loads(event["genres"]) if event["genres"] else []
    return f"""Title: {event['title']}
Venue: {event['venue']}
City: {event['city']}
Date: {event['event_date']}
Lineup: {', '.join(lineup) if lineup else 'Not listed'}
Genres: {', '.join(genres) if genres else 'Not listed'}
Raw description: {event['raw_description']}"""


def review_pending_events():
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    with get_db() as conn:
        pending = conn.execute(
            "SELECT * FROM events WHERE status = 'pending' AND ai_summary IS NULL"
        ).fetchall()

    if not pending:
        print("No events need AI review right now.")
        return

    print(f"Reviewing {len(pending)} events...")

    for event in pending:
        user_prompt = build_user_prompt(event)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = response.content[0].text.strip()

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            print(f"  ⚠ Could not parse AI response for event {event['id']}, skipping.")
            continue

        with get_db() as conn:
            conn.execute(
                """
                UPDATE events
                SET ai_summary = ?, ai_verdict = ?, ai_reasoning = ?
                WHERE id = ?
                """,
                (
                    parsed.get("summary", ""),
                    parsed.get("verdict", "needs_review"),
                    parsed.get("reasoning", ""),
                    event["id"],
                ),
            )

        print(f"  ✓ {event['title']} → {parsed.get('verdict')}")

    print("Done. Open the approval panel to review and publish.")


if __name__ == "__main__":
    init_db()
    review_pending_events()
