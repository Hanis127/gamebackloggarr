from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse, RedirectResponse
import sqlite3
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/games/{game_id}/vote/{value}")
async def vote(
    game_id: int = Path(...),
    value: int = Path(...),
    user=Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db)
):
    if value not in (-1, 1):
        return JSONResponse({"error": "Invalid vote"}, status_code=400)

    existing = db.execute(
        "SELECT value FROM votes WHERE game_id=? AND user_id=?",
        (game_id, user["id"])
    ).fetchone()

    if existing:
        if existing["value"] == value:
            # Toggle off
            db.execute("DELETE FROM votes WHERE game_id=? AND user_id=?", (game_id, user["id"]))
        else:
            db.execute(
                "UPDATE votes SET value=? WHERE game_id=? AND user_id=?",
                (value, game_id, user["id"])
            )
    else:
        db.execute(
            "INSERT INTO votes (game_id, user_id, value) VALUES (?,?,?)",
            (game_id, user["id"], value)
        )

    db.commit()

    score = db.execute(
        "SELECT COALESCE(SUM(value),0) as s FROM votes WHERE game_id=?",
        (game_id,)
    ).fetchone()["s"]

    my_vote = db.execute(
        "SELECT value FROM votes WHERE game_id=? AND user_id=?",
        (game_id, user["id"])
    ).fetchone()

    return JSONResponse({
        "score": score,
        "my_vote": my_vote["value"] if my_vote else 0
    })
