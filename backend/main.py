"""Golf Scoring App - FastAPI Backend."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# CORS - allow frontend
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(players.router)
app.include_router(courses.router)
app.include_router(games.router)
app.include_router(leagues.router)
app.include_router(seed.router)


@app.get("/")
async def root():
    return {"message": "Golf Scoring App API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
