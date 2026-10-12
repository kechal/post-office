import os
import re
import secrets
import smtplib
import sqlite3
from email.message import EmailMessage

from flask import Flask, abort, g, redirect, render_template, request, url_for

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "post_office.db")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_MESSAGE = 2000


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS cards (
            id TEXT PRIMARY KEY,
            to_email TEXT NOT NULL,
            from_name TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def send_email(to_email, from_name, link):
    """Sends the link by email if SMTP_* env vars are set.
    Otherwise it just prints the email to the terminal."""
    subject = f"{from_name} sent you a card!"
    body = f"{from_name} sent you a card through The Post Office! \n\nOpen it here:\n{link}\n"

    host = os.environ.get("SMTP_HOST")
    if not host:
        print("\n--- email (not actually sent: SMTP_HOST is not set) ---")
        print(f"To: {to_email}\nSubject: {subject}\n\n{body}")
        return

    msg = EmailMessage()
    msg["From"] = os.environ.get("SMTP_FROM", os.environ.get("SMTP_USER", ""))
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", 587))) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(msg)


@app.get("/")
def index():
    return render_template("index.html", values={}, error=None, max_message=MAX_MESSAGE)


@app.post("/send")
def send():
    values = {
        "to_email": request.form.get("to_email", "").strip(),
        "message": request.form.get("message", "").strip(),
        "from_name": request.form.get("from_name", "").strip(),
    }
    error = None
    if not EMAIL_RE.match(values["to_email"]):
        error = "Invalid email address"
    elif not values["message"]:
        error = "Message is required"
    elif not values["from_name"]:
        error = "Your name is required"
    if error:
        return render_template("index.html", values=values, error=error, max_message=MAX_MESSAGE), 400

    card_id = secrets.token_urlsafe(8)
    get_db().execute(
        "INSERT INTO cards (id, to_email, from_name, message) VALUES (?, ?, ?, ?)",
        (card_id, values["to_email"], values["from_name"], values["message"]),
    )
    get_db().commit()

    link = url_for("card", card_id=card_id, _external=True)
    try:
        send_email(values["to_email"], values["from_name"], link)
    except Exception as exc:
        print(f"Error sending email: {exc}")
        return redirect(url_for("sent", card_id=card_id, email_failed=1))
    return redirect(url_for("sent", card_id=card_id))


@app.get("/sent/<card_id>")
def sent(card_id):
    row = get_db().execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if row is None:
        abort(404)
    return render_template(
        "sent.html",
        card=row,
        link=url_for("card", card_id=card_id, _external=True),
        email_failed=request.args.get("email_failed"),
    )


@app.get("/card/<card_id>")
def card(card_id):
    row = get_db().execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if row is None:
        abort(404)
    return render_template("card.html", card=row)


@app.errorhandler(404)
def not_found(_e):
    return render_template("not_found.html"), 404


init_db()

if __name__ == "__main__":
    app.run(debug=True)

