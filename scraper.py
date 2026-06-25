"""
Undercurrent — Event scraper

IMPORTANT — read before connecting a real source:
Resident Advisor has no official public API. Third-party scraping (e.g. via
Apify actors) is commonly used, but RA's own terms flag commercial use of
scraped data as something you need their permission for. Treat this script
as the *shape* of the pipeline — plug in your chosen data source responsibly:

  - For testing: use the bundled `fetch_sample_events()` (fake data, no network calls)
  - For real RA data: use an Apify actor (apify.com) with your own API token,
    or RA's own "submit event" partnerships if you reach out to them directly
  - For Instagram: there is no reliable free scraping path. Most production
    setups use a paid provider (Apify, Bright Data) and break often. Consider
    this the lowest-priority, highest-maintenance source.

Run manually with: python scraper.py
Or schedule with cron, e.g. every day at 9am:
    0 9 * * * cd /path/to/undercurrent-app && python scraper.py
"""
import json
import os
from datetime import datetime, timedelta
from models import get_db, init_db


def fetch_sample_events():
    """
    Placeholder data source so the pipeline runs end-to-end without any
    API keys. Replace this function's body with a real fetch once you've
    chosen and configured a provider.
    """
    today = datetime.now()
    return [
        {
            "source": "resident_advisor",
            "source_id": "ra-demo-001",
            "title": "Subterrane: Object Permanence Label Night",
            "venue": "Elsewhere",
            "city": "Brooklyn, NY",
            "event_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "lineup": ["Object Permanence", "Hyperdub NYC", "DJ Tako"],
            "genres": ["Techno", "Electro"],
            "ticket_url": "https://example.com/tickets/ra-demo-001",
            "raw_description": "Label showcase featuring a tightly curated lineup of "
                                "electro and techno acts. Limited capacity room, "
                                "known for serious sound systems and no phones policy.",
        },
        {
            "source": "resident_advisor",
            "source_id": "ra-demo-002",
            "title": "Saturdays — Open Format Rooftop",
            "venue": "Untitled Rooftop",
            "city": "Jersey City, NJ",
            "event_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "lineup": ["DJ Marco", "Resident Selecta"],
            "genres": ["Open Format", "Commercial House"],
            "ticket_url": "https://example.com/tickets/ra-demo-002",
            "raw_description": "Weekly rooftop party, open format mix of commercial "
                                "house and top 40 remixes. Bottle service available.",
        },
        {
            "source": "manual",
            "source_id": "manual-001",
            "title": "Concrete Hours w/ DVS1",
            "venue": "Public Records",
            "city": "Brooklyn, NY",
            "event_date": (today + timedelta(days=12)).strftime("%Y-%m-%d"),
            "lineup": ["DVS1", "Local Support TBA"],
            "genres": ["Techno", "Minimal"],
            "ticket_url": "https://example.com/tickets/manual-001",
            "raw_description": "DVS1's first NYC appearance in over a year. Public "
                                "Records' system is one of the best-tuned rooms on "
                                "the east coast. Early presale moves fast.",
        },
    ]


def save_events(events):
    """Insert new events, skipping any we've already seen (by source + source_id)."""
    new_count = 0
    with get_db() as conn:
        for ev in events:
            existing = conn.execute(
                "SELECT id FROM events WHERE source = ? AND source_id = ?",
                (ev["source"], ev["source_id"]),
            ).fetchone()
            if existing:
                continue

            conn.execute(
                """
                INSERT INTO events
                    (source, source_id, title, venue, city, event_date,
                     lineup, genres, ticket_url, raw_description, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                (
                    ev["source"],
                    ev["source_id"],
                    ev["title"],
                    ev["venue"],
                    ev["city"],
                    ev["event_date"],
                    json.dumps(ev["lineup"]),
                    json.dumps(ev["genres"]),
                    ev["ticket_url"],
                    ev["raw_description"],
                ),
            )
            new_count += 1
    return new_count


def run():
    init_db()
    events = fetch_sample_events()
    new_count = save_events(events)
    print(f"Scraped {len(events)} events, {new_count} new (rest were duplicates).")
    print("Next step: run `python ai_review.py` to generate editorial summaries,")
    print("then open the approval panel at /admin to review before publishing.")


if __name__ == "__main__":
    run()
