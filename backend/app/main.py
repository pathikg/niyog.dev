from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine

# TODO: Import routers when ready
# from app.api.routers import auth, hr_schema, hr_profiles, talent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown"""
    # Startup
    print("🚀 Starting Niyog server...")
    # Initialize LangGraph checkpointer
    # TODO: await checkpointer.setup()

    yield

    # Shutdown
    print("🛑 Shutting down Niyog server...")
    await engine.dispose()


app = FastAPI(
    title="Niyog",
    description="Multi-tenant HR talent onboarding platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else ["https://niyog.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# Include routers (when ready)
# app.include_router(auth.router)
# app.include_router(hr_schema.router)
# app.include_router(hr_profiles.router)
# app.include_router(talent.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
