import httpx
import os
import time
from typing import Optional

IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID", "")
IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET", "")

_token_cache = {"access_token": None, "expires_at": 0}


async def get_igdb_token() -> Optional[str]:
    if not IGDB_CLIENT_ID or not IGDB_CLIENT_SECRET:
        return None
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["access_token"]
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://id.twitch.tv/oauth2/token",
            params={
                "client_id": IGDB_CLIENT_ID,
                "client_secret": IGDB_CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
        )
        data = resp.json()
        _token_cache["access_token"] = data["access_token"]
        _token_cache["expires_at"] = now + data["expires_in"]
        return _token_cache["access_token"]


def _cover_url(image_id: str, size: str = "cover_big") -> str:
    return f"https://images.igdb.com/igdb/image/upload/t_{size}/{image_id}.jpg"


async def search_games(query: str, limit: int = 8) -> list[dict]:
    token = await get_igdb_token()
    if not token:
        return []
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.igdb.com/v4/games",
            headers={"Client-ID": IGDB_CLIENT_ID, "Authorization": f"Bearer {token}"},
            content=f"""
                fields id, name, cover.image_id, first_release_date, genres.name, platforms.name, summary, rating;
                search "{query}";
                where version_parent = null;
                limit {limit};
            """,
        )
    results = []
    for g in resp.json():
        cover = None
        if "cover" in g and g["cover"]:
            cover = _cover_url(g["cover"]["image_id"])
        year = None
        if "first_release_date" in g:
            year = time.strftime("%Y", time.gmtime(g["first_release_date"]))
        genres = ", ".join(x["name"] for x in g.get("genres", []))
        platforms = ", ".join(x["name"] for x in g.get("platforms", []))
        results.append({
            "igdb_id": g["id"],
            "title": g["name"],
            "cover_url": cover,
            "summary": g.get("summary", "")[:500] if g.get("summary") else "",
            "genres": genres,
            "platforms": platforms,
            "release_year": year,
            "rating": round(g["rating"] / 10, 1) if g.get("rating") else None,
        })
    return results
