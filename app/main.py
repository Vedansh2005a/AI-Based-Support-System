
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.guardrails.service import process_support_message
from pathlib import Path
from typing import Literal

from fastapi.responses import FileResponse

from app.support.ticket_service import (
    list_support_tickets,
    update_ticket_status,
)
from pathlib import Path

from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI-Based Customer Support System",
    description="Customer support with RAG, Guardrails, and human handoff",
    version="1.1.0",
)
BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)

class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Customer's support question",
    )


class ChatResponse(BaseModel):
    response: str
    handoff: bool = False
    ticket_id: str | None = None
    department: str | None = None
    ticket_status: str | None = None

class TicketStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved"]

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "customer-support-api",
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await process_support_message(
            request.message
        )
        return ChatResponse(**result)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception("Chat API request failed")

        raise HTTPException(
            status_code=503,
            detail="The support service is temporarily unavailable.",
        ) from exc


DASHBOARD_PATH = (
    Path(__file__).resolve().parent
    / "dashboard"
    / "index.html"
)





@app.get("/api/tickets")
async def get_support_tickets(
    status: Literal["open", "in_progress", "resolved"] | None = None,
    department: str | None = None,
):
    try:
        tickets = list_support_tickets(
            status=status,
            department=department,
        )
        return {"tickets": tickets}

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@app.patch("/api/tickets/{ticket_id}/status")
async def change_ticket_status(
    ticket_id: str,
    request: TicketStatusUpdate,
):
    try:
        ticket = update_ticket_status(
            ticket_id=ticket_id,
            status=request.status,
        )

        if ticket is None:
            raise HTTPException(
                status_code=404,
                detail="Ticket not found.",
            )

        return ticket

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.get("/dashboard", include_in_schema=False)
async def support_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={},
    )

@app.get("/chat", include_in_schema=False)
async def chat_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={},
    )