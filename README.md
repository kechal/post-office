# The Post Office

A demo Flask app!!

## Run locally

You need Python 3.9 or newer to run this progam. From the repository root, open a terminal and run:

```powershell
cd terra\real
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

On macOS or Linux, use `python3` to create the virtual environment and activate it
with `source .venv/bin/activate`.

Open <http://127.0.0.1:5000> in your browser. When you submit a card, the app
prints a preview of the email and its link in the terminal; it does not send a
real email unless SMTP settings are edited and configured.

## Optional email setup

To send email, copy `run-local.ps1.example` to `run-local.ps1`, replace the
example values with your SMTP settings, and run `.\run-local.ps1` in PowerShell
before starting the app. For Gmail, use an App Password. Keep real credentials
in `run-local.ps1` and never commit that file!

This is for local development and testing, not a production web server. :3
