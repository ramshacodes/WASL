"""
Vercel serverless entrypoint. Vercel's Python runtime looks for an ASGI-
compatible `app` object in this file — FastAPI's app is already ASGI, so we
just re-export it. All actual routes/logic still live in app/main.py.
"""
from app.main import app  # noqa: F401
