from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, health
from app.database import async_session, engine
from app.services.seed import seed_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session() as db:
        await seed_users(db)
    yield
    await engine.dispose()


app = FastAPI(title="Niyog", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router, prefix="/api")
