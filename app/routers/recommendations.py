from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from app.database import get_db
from app.dependencies import get_current_user, get_current_user_optional
from app.igdb import get_similar_games

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/recommendations", response_class=HTMLResponse)
async def recommendations_page(
    request: Request,
    user=Depends(get_current_user_optional),
    db: sqlite3.Connection = Depends(get_db)
):
    if not user:
        return RedirectResponse("/login", status_code=302)

    # Get all games in backlog (not completed/dropped) with their IGDB IDs
    rows = db.execute("""
        SELECT igdb_id, title FROM games
        WHERE igdb_id IS NOT NULL AND status NOT IN ('completed', 'dropped')
        ORDER BY created_at DESC
    """).fetchall()

    already_have_ids = set(
        r["igdb_id"] for r in db.execute("SELECT igdb_id FROM games WHERE igdb_id IS NOT NULL").fetchall()
    )

    backlog_games = [dict(r) for r in rows]
    igdb_ids = [r["igdb_id"] for r in backlog_games]

    recommendations = []
    no_igdb = len(igdb_ids) == 0
    igdb_error = False

    if igdb_ids:
        try:
            recommendations = await get_similar_games(igdb_ids, already_have_ids)
        except Exception as e:
            igdb_error = True

    return templates.TemplateResponse("recommendations.html", {
        "request": request,
        "user": user,
        "recommendations": recommendations,
        "backlog_games": backlog_games,
        "no_igdb": no_igdb,
        "igdb_error": igdb_error,
    })
