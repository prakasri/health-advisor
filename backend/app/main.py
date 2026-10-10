from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.ratelimit import limiter
from app.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Health Advisor API", version="1.0.0")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(router)
    return app


app = create_app()
