import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import interactions, off, products, recommendations

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        logger.info("Database connected and tables ready.")
    except Exception as exc:
        logger.warning(
            "Database unavailable (%s). "
            "API endpoints will fail until a DB is configured. "
            "Frontend is still served.",
            exc,
        )
    yield


app = FastAPI(title="EcoScan API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict to your domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(interactions.router)
app.include_router(recommendations.router)
app.include_router(off.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve the frontend — must be mounted last, after all API routes
_FRONTEND_DIR = str(Path(__file__).parent.parent.parent / "frontend")
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
