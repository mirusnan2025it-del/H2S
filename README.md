# H2S Smart Wristband

A Flask demo for H2S exposure monitoring workflows. It includes worker and manager dashboards, image-based indicator-strip analysis, a simulator, and detection history.

> **Demo only:** This project is not a certified gas detector or a substitute for calibrated safety equipment, workplace procedures, or emergency response. Do not rely on it to determine whether an area is safe.

## Run locally

Requirements: Python 3.10 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> in your browser. On the login page, use the built-in demo buttons to fill a sample manager or worker account.

## Deploy to Render

1. Push this project to a GitHub repository. Keep the local virtual environment, database, and uploads out of Git; the included `.gitignore` excludes them.
2. In Render, choose **New** > **Blueprint** and connect the GitHub repository.
3. Render reads `render.yaml` to install dependencies, generate a secret key, and start the Flask app.
4. When deployment finishes, open the `onrender.com` URL from a phone, tablet, or computer.

The app uses SQLite. On a standard Render web service, local database files are not durable across restarts or deployments, so demo users and records may be reset. Do not use this setup for real worker accounts, personal data, or production records.

## Configuration

- `SECRET_KEY`: Flask session signing key. Render generates this for the hosted service.
- `DATABASE_PATH`: optional path to the SQLite database. Defaults to `database/h2s_wristband.db` in the project folder.
