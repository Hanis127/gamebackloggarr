from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import hashlib, secrets, sqlite3
from app.database import get_db
from app.dependencies import get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user=Depends(get_current_user_optional)):
    if user:
        return RedirectResponse("/games", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT id, username FROM users WHERE username=? AND password_hash=?",
        (username.strip(), hash_password(password))
    ).fetchone()
    if not row:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})
    token = secrets.token_hex(32)
    db.execute("INSERT INTO sessions (token, user_id) VALUES (?,?)", (token, row["id"]))
    db.commit()
    resp = RedirectResponse("/games", status_code=302)
    resp.set_cookie("session", token, httponly=True, samesite="lax")
    return resp


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user=Depends(get_current_user_optional)):
    if user:
        return RedirectResponse("/games", status_code=302)
    # Check if registration is allowed (max 2 users)
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), password: str = Form(...), invite_code: str = Form(...), db: sqlite3.Connection = Depends(get_db)):
    import os
    expected = os.getenv("INVITE_CODE", "changeme")
    if invite_code.strip() != expected:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Invalid invite code"})
    count = db.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    if count >= 2:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Max users reached (2). Ask your co-op partner to remove an account."})
    username = username.strip()
    if not username or len(username) < 2:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username too short"})
    existing = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already taken"})
    db.execute("INSERT INTO users (username, password_hash) VALUES (?,?)", (username, hash_password(password)))
    db.commit()
    return RedirectResponse("/login", status_code=302)


@router.get("/logout")
async def logout(request: Request, db: sqlite3.Connection = Depends(get_db)):
    token = request.cookies.get("session")
    if token:
        db.execute("DELETE FROM sessions WHERE token=?", (token,))
        db.commit()
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("session")
    return resp
