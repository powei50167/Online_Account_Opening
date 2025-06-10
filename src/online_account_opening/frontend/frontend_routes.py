# src/online_account_opening/frontend/frontend_routes.py

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import pathlib

router = APIRouter()

# index.html 路徑
BASE_DIR = pathlib.Path(__file__).resolve().parent
HTML_PATH = BASE_DIR / "index.html"

@router.get("/", response_class=HTMLResponse)
def get_index():
    with open(HTML_PATH, encoding="utf-8") as f:
        return f.read()
