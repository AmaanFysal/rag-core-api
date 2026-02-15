from fastapi import FastAPI
from app.api.routes.health import router as health_router
from app.api.routes.document import router as document_router
from app.api.routes.search import router as search_router
from app.api.routes.ask import router as ask_router

app = FastAPI(title="AI Knowledge Assistant API")

app.include_router(health_router)
app.include_router(document_router)
app.include_router(search_router)
app.include_router(ask_router)