from fastapi import Request, Depends
from app.database import get_db
import sqlite3


def get_current_user_optional(request: Request, db: sqlite3.Connection = Depends(get_db)):
    token = request.cookies.get("session")
    if not token:
        return None
    row = db.execute(
        "SELECT u.id, u.username FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?",
        (token,)
    ).fetchone()
    return dict(row) if row else None


def get_current_user(request: Request, db: sqlite3.Connection = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        from fastapi.responses import RedirectResponse
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
