from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.ratelimit import limiter
from app.api.routes import router
from app.graph.graph import assessment_graph
from app.tracing import setup_tracing


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    setup_tracing()
    assessment_graph()  # compile once at start-up; fails fast on spec/prompt errors
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Health Advisor API", version="1.0.0", lifespan=lifespan)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(router)
    return app


app = create_app()
