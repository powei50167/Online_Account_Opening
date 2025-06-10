from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from online_account_opening.api.routes import router as api_router
from online_account_opening.frontend.frontend_routes import router as frontend_router
import pathlib

app = FastAPI()

# 路徑設定
BASE_DIR = pathlib.Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "frontend" / "static"

# 掛載靜態檔案
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 掛載路由
app.include_router(frontend_router)             # 不加 prefix，直接處理 "/"
app.include_router(api_router, prefix="/api")   # 加 prefix，處理 API
