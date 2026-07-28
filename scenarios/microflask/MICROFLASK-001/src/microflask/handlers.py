"""Request handlers for MicroFlask API.

BUG: Pagination off-by-one. Page 1 should return items 1-10 but the
formula `page * per_page` skips the first per_page items because
offset starts at per_page instead of 0.
"""

import json
import db
import os

_PER_PAGE_DEFAULT = 10


def handle_request(environ):
    """Route a WSGI request to the appropriate handler."""
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")

    if path == "/health" and method == "GET":
        return handle_health()
    if path == "/items" and method == "GET":
        return handle_list_items(environ)
    if path.startswith("/items/") and method == "GET":
        item_id = path.split("/")[-1]
        return handle_get_item(item_id)
    if path == "/items" and method == "POST":
        return handle_create_item(environ)
    return (404, {"error": "not found"})


def handle_health():
    """Health check - reports service and database status."""
    try:
        conn = db.get_db()
        conn.execute("SELECT 1")
        return (200, {"status": "healthy"})
    except Exception as exc:
        return (503, {"status": "unhealthy", "reason": str(exc)})


def handle_list_items(environ):
    """List items with pagination.

    BUG: offset = page * per_page instead of (page-1) * per_page.
    This causes the first page to skip items 1-10.
    """
    params = _parse_query(environ.get("QUERY_STRING", ""))
    page = int(params.get("page", "1"))
    per_page = int(params.get("per_page", str(_PER_PAGE_DEFAULT)))

    # BUG: This should be (page - 1) * per_page
    offset = page * per_page

    conn = db.get_db()
    cursor = conn.execute(
        "SELECT id, name, price, created_at FROM items "
        "ORDER BY id LIMIT ? OFFSET ?",
        (per_page, offset),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    cursor_total = conn.execute("SELECT COUNT(*) as count FROM items")
    total = cursor_total.fetchone()["count"]
    return (200, {
        "items": rows,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
    })


def handle_get_item(item_id):
    """Get a single item by ID."""
    try:
        conn = db.get_db()
        cursor = conn.execute("SELECT id, name, price, created_at FROM items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if row is None:
            return (404, {"error": "not found"})
        return (200, dict(row))
    except Exception as exc:
        return (500, {"error": str(exc)})


def handle_create_item(environ):
    """Create a new item."""
    try:
        body = _read_body(environ)
        data = json.loads(body)
        conn = db.get_db()
        cursor = conn.execute(
            "INSERT INTO items (name, price) VALUES (?, ?)",
            (data["name"], float(data["price"])),
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor = conn.execute("SELECT id, name, price, created_at FROM items WHERE id = ?", (new_id,))
        return (201, dict(cursor.fetchone()))
    except Exception as exc:
        return (400, {"error": str(exc)})


def _parse_query(qs):
    params = {}
    for part in qs.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k] = v
    return params


def _read_body(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH", "0"))
    except ValueError:
        length = 0
    body = environ.get("wsgi.input", b"")
    if hasattr(body, "read"):
        return body.read(length).decode("utf-8")
    return ""
