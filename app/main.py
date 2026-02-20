from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.document import router as document_router
from app.api.routes.search import router as search_router
from app.api.routes.ask import router as ask_router
from app.core.limiter import limiter
from app.middleware.size_limit import RequestSizeLimitMiddleware

app = FastAPI(title="AI Knowledge Assistant API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestSizeLimitMiddleware)

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(document_router)
app.include_router(search_router)
app.include_router(ask_router)
