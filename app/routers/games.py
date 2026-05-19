from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import sqlite3, json
from app.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.igdb import search_games

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

STATUSES = ["backlog", "playing", "completed", "dropped"]


@router.get("/games", response_class=HTMLResponse)
async def games_list(
    request: Request,
    status: str = "backlog",
    sort: str = "votes",
    user=Depends(get_current_user_optional),
    db: sqlite3.Connection = Depends(get_db)
):
    if not user:
        return RedirectResponse("/login", status_code=302)

    if status not in STATUSES:
        status = "backlog"

    sort_clause = {
        "votes": "vote_score DESC, g.created_at DESC",
        "newest": "g.created_at DESC",
        "title": "g.title ASC",
        "rating": "g.rating DESC NULLS LAST",
    }.get(sort, "vote_score DESC")

    rows = db.execute(f"""
        SELECT g.*,
               u.username as suggested_by_name,
               COALESCE(SUM(v.value), 0) as vote_score,
               (SELECT v2.value FROM votes v2 WHERE v2.game_id = g.id AND v2.user_id = ?) as my_vote
        FROM games g
        LEFT JOIN users u ON u.id = g.suggested_by
        LEFT JOIN votes v ON v.game_id = g.id
        WHERE g.status = ?
        GROUP BY g.id
        ORDER BY {sort_clause}
    """, (user["id"], status)).fetchall()

    games = [dict(r) for r in rows]

    counts = {}
    for s in STATUSES:
        counts[s] = db.execute("SELECT COUNT(*) as c FROM games WHERE status=?", (s,)).fetchone()["c"]

    all_users = db.execute("SELECT username FROM users").fetchall()

    return templates.TemplateResponse("games.html", {
        "request": request,
        "user": user,
        "games": games,
        "status": status,
        "sort": sort,
        "statuses": STATUSES,
        "counts": counts,
        "users": [r["username"] for r in all_users],
    })


@router.get("/api/igdb/search")
async def igdb_search(q: str = Query(..., min_length=2), user=Depends(get_current_user_optional)):
    if not user:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    results = await search_games(q)
    return JSONResponse(results)


@router.post("/games/add")
async def add_game(
    request: Request,
    igdb_id: int = Form(...),
    title: str = Form(...),
    cover_url: str = Form(""),
    summary: str = Form(""),
    genres: str = Form(""),
    platforms: str = Form(""),
    release_year: str = Form(""),
    rating: str = Form(""),
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    existing = db.execute("SELECT id FROM games WHERE igdb_id=?", (igdb_id,)).fetchone()
    if existing:
        return RedirectResponse("/games?error=already_added", status_code=302)

    db.execute("""
        INSERT INTO games (igdb_id, title, cover_url, summary, genres, platforms, release_year, rating, suggested_by)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        igdb_id, title, cover_url or None, summary or None,
        genres or None, platforms or None,
        int(release_year) if release_year else None,
        float(rating) if rating else None,
        user["id"]
    ))
    db.commit()
    return RedirectResponse("/games", status_code=302)


@router.post("/games/{game_id}/status")
async def update_status(
    game_id: int,
    status: str = Form(...),
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    if status not in STATUSES:
        return RedirectResponse("/games", status_code=302)
    db.execute("UPDATE games SET status=? WHERE id=?", (status, game_id))
    db.commit()
    return RedirectResponse("/games", status_code=302)


@router.post("/games/{game_id}/delete")
async def delete_game(
    game_id: int,
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    db.execute("DELETE FROM games WHERE id=?", (game_id,))
    db.commit()
    return RedirectResponse("/games", status_code=302)
