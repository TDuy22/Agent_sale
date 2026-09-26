import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.chat import router as chat_router
from app.api.routes.sessions import router as sessions_router
from app.domain.exceptions import ConversationNotFoundError, DomainError
from app.settings import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level.upper())

app = FastAPI(title="Interior Quotation Chatbot", version="0.1.0")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(ConversationNotFoundError)
def conversation_not_found(_request: Request, exc: ConversationNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(DomainError)
def domain_error(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})
