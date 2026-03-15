"""Golf Scoring App - FastAPI Backend."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import init_db
from routers import players, courses, games, leagues, seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Golf Scoring App",
    description="Multi-format golf scoring with live leaderboards and Order of Merit",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Register API routers FIRST
app.include_router(players.router)
app.include_router(courses.router)
app.include_router(games.router)
app.include_router(leagues.router)
app.include_router(seed.router)


# Serve frontend static files AFTER API routes
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Never intercept API routes
        if full_path.startswith("api"):
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
