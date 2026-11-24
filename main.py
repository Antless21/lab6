"""Точка входа FastAPI: python -m uvicorn main:app --reload."""

from lab6.api import create_app

app = create_app()
