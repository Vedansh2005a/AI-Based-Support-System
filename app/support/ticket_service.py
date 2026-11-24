
import sqlite3
import uuid

from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "support_tickets.db"


DEPARTMENT_RULES = [
    (
        "Returns & Refunds",
        (
            "refund",
            "return item",
            "return policy",
            "exchange",
            "cancel my order",
            "order cancellation",
        ),
    ),
    (
        "Billing & Payments",
        (
            "payment",
            "billing",
            "invoice",
            "charged",
            "charge",
            "transaction",
            "credit card",
            "debit card",
        ),
    ),
    (
        "Orders & Shipping",
        (
            "shipping",
            "shipment",
            "delivery",
            "tracking",
            "track my order",
            "order status",
            "package",
        ),
    ),
    (
        "Account & Security",
        (
            "account",
            "login",
            "log in",
            "sign in",
            "password",
            "security",
            "locked out",
        ),
    ),
    (
        "Subscription Support",
        (
            "subscription",
            "renewal",
            "membership",
        ),
    ),
    (
        "Technical Support",
        (
            "technical issue",
            "error",
            "bug",
            "crash",
            "not working",
            "installation",
            "setup",
            "app issue",
        ),
    ),
    (
        "Product & Warranty",
        (
            "warranty",
            "defective",
            "damaged product",
            "product issue",
        ),
    ),
]


def initialize_ticket_db():
    """Create the SQLite ticket table if it does not exist."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE NOT NULL,
                customer_message TEXT NOT NULL,
                department TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL
            )
            """
        )


def assign_department(message: str) -> str:
    """Assign a department using simple keyword rules."""

    text = message.lower()

    for department, keywords in DEPARTMENT_RULES:
        if any(keyword in text for keyword in keywords):
            return department

    return "General Customer Support"


def create_support_ticket(message: str, reason: str) -> dict:
    """Persist a support ticket and return its details."""

    if not isinstance(message, str) or not message.strip():
        raise ValueError("Customer message must not be empty.")

    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("Ticket reason must not be empty.")

    initialize_ticket_db()

    ticket_id = f"SUP-{uuid.uuid4().hex[:8].upper()}"
    department = assign_department(message)
    created_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        connection.execute(
            """
            INSERT INTO support_tickets (
                ticket_id,
                customer_message,
                department,
                reason,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                message.strip(),
                department,
                reason.strip(),
                "open",
                created_at,
            ),
        )

    return {
        "ticket_id": ticket_id,
        "department": department,
        "reason": reason,
        "status": "open",
        "created_at": created_at,
    }


def list_support_tickets(
    status: str | None = None,
    department: str | None = None,
) -> list[dict]:
    """Return support tickets, optionally filtered."""

    initialize_ticket_db()

    query = """
        SELECT ticket_id, customer_message, department,
               reason, status, created_at
        FROM support_tickets
    """
    conditions = []
    params = []

    if status:
        if status not in {"open", "in_progress", "resolved"}:
            raise ValueError("Invalid ticket status.")
        conditions.append("status = ?")
        params.append(status)

    if department:
        conditions.append("department = ?")
        params.append(department)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC"

    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, params).fetchall()

    return [dict(row) for row in rows]


def update_ticket_status(
    ticket_id: str,
    status: str,
) -> dict | None:
    """Update a ticket's status. Return None if not found."""

    allowed_statuses = {"open", "in_progress", "resolved"}

    if status not in allowed_statuses:
        raise ValueError("Invalid ticket status.")

    initialize_ticket_db()

    with sqlite3.connect(DB_PATH, timeout=10) as connection:
        connection.row_factory = sqlite3.Row

        cursor = connection.execute(
            """
            UPDATE support_tickets
            SET status = ?
            WHERE ticket_id = ?
            """,
            (status, ticket_id),
        )

        if cursor.rowcount == 0:
            return None

        row = connection.execute(
            """
            SELECT ticket_id, customer_message, department,
                   reason, status, created_at
            FROM support_tickets
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

    return dict(row) if row else None
