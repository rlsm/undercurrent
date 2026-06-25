"""
Undercurrent — Flask app
Serves both the public site (/) and the approval panel (/admin)

Run with: python app.py
Then visit:
  http://localhost:5000        — public site
  http://localhost:5000/admin  — approval panel (protect this in production!)
"""
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
from models import get_db, init_db

app = Flask(__name__)

# Initialize the database on startup — this runs both when you do
# `python app.py` locally AND when gunicorn imports this file on Render.
init_db()


def parse_event_row(row):
    """Convert a sqlite Row into a plain dict with JSON fields decoded."""
    d = dict(row)
    d["lineup"] = json.loads(d["lineup"]) if d.get("lineup") else []
    d["genres"] = json.loads(d["genres"]) if d.get("genres") else []
    return d


# ---------- Public site ----------

@app.route("/")
def home():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM events
            WHERE status = 'approved'
            ORDER BY event_date ASC
            """
        ).fetchall()
    events = [parse_event_row(r) for r in rows]
    return render_template("public.html", events=events)


@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email", "").strip().lower()
    tier = request.form.get("tier", "free")

    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "Enter a valid email."}), 400

    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM subscribers WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            return jsonify({"ok": True, "message": "You're already on the list."})

        draw_entries = 5 if tier == "member" else 1
        conn.execute(
            "INSERT INTO subscribers (email, tier, draw_entries) VALUES (?, ?, ?)",
            (email, tier, draw_entries),
        )

    return jsonify({"ok": True, "message": "You're in."})


# ---------- Admin / approval panel ----------

@app.route("/admin")
def admin_panel():
    with get_db() as conn:
        pending = conn.execute(
            "SELECT * FROM events WHERE status = 'pending' ORDER BY scraped_at DESC"
        ).fetchall()
        approved = conn.execute(
            "SELECT * FROM events WHERE status = 'approved' ORDER BY event_date ASC"
        ).fetchall()
        rejected = conn.execute(
            "SELECT * FROM events WHERE status = 'rejected' ORDER BY scraped_at DESC LIMIT 20"
        ).fetchall()

    return render_template(
        "admin.html",
        pending=[parse_event_row(r) for r in pending],
        approved=[parse_event_row(r) for r in approved],
        rejected=[parse_event_row(r) for r in rejected],
    )


@app.route("/admin/event/<int:event_id>/approve", methods=["POST"])
def approve_event(event_id):
    editor_note = request.form.get("editor_note", "")
    with get_db() as conn:
        conn.execute(
            """
            UPDATE events
            SET status = 'approved', reviewed_at = ?, published_at = ?, editor_note = ?
            WHERE id = ?
            """,
            (datetime.now().isoformat(), datetime.now().isoformat(), editor_note, event_id),
        )
    return redirect(url_for("admin_panel"))


@app.route("/admin/event/<int:event_id>/reject", methods=["POST"])
def reject_event(event_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE events SET status = 'rejected', reviewed_at = ? WHERE id = ?",
            (datetime.now().isoformat(), event_id),
        )
    return redirect(url_for("admin_panel"))


@app.route("/admin/event/<int:event_id>/edit", methods=["POST"])
def edit_event(event_id):
    """Let Ronald override the AI-written summary before approving."""
    new_summary = request.form.get("ai_summary", "")
    with get_db() as conn:
        conn.execute(
            "UPDATE events SET ai_summary = ? WHERE id = ?",
            (new_summary, event_id),
        )
    return redirect(url_for("admin_panel"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
