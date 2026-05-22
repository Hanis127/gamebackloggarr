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


async def get_similar_games(igdb_ids: list[int], already_have: set[int], limit_per_game: int = 5) -> list[dict]:
    """Fetch similar_games for a list of IGDB IDs, return ranked deduplicated results."""
    token = await get_igdb_token()
    if not token or not igdb_ids:
        return []

    ids_str = ",".join(str(i) for i in igdb_ids[:20])  # cap at 20 source games

    async with httpx.AsyncClient() as client:
        # Step 1: get similar_game IDs for our backlog games
        resp = await client.post(
            "https://api.igdb.com/v4/games",
            headers={"Client-ID": IGDB_CLIENT_ID, "Authorization": f"Bearer {token}"},
            content=f"""
                fields id, name, similar_games;
                where id = ({ids_str});
                limit 20;
            """,
        )

    # Tally how many backlog games recommend each candidate
    tally: dict[int, int] = {}
    source_names: dict[int, list[str]] = {}
    games_by_id = {g["id"]: g.get("name", "") for g in resp.json()}

    for g in resp.json():
        for sim_id in g.get("similar_games", []):
            if sim_id not in already_have and sim_id not in igdb_ids:
                tally[sim_id] = tally.get(sim_id, 0) + 1
                source_names.setdefault(sim_id, []).append(games_by_id.get(g["id"], ""))

    if not tally:
        return []

    # Take top 20 by tally score
    top_ids = sorted(tally, key=lambda x: -tally[x])[:20]
    ids_str2 = ",".join(str(i) for i in top_ids)

    async with httpx.AsyncClient() as client:
        resp2 = await client.post(
            "https://api.igdb.com/v4/games",
            headers={"Client-ID": IGDB_CLIENT_ID, "Authorization": f"Bearer {token}"},
            content=f"""
                fields id, name, cover.image_id, first_release_date, genres.name, platforms.name, summary, rating;
                where id = ({ids_str2}) & version_parent = null;
                limit 20;
            """,
        )

    results = []
    for g in resp2.json():
        cover = None
        if g.get("cover"):
            cover = _cover_url(g["cover"]["image_id"])
        year = None
        if "first_release_date" in g:
            year = time.strftime("%Y", time.gmtime(g["first_release_date"]))
        genres = ", ".join(x["name"] for x in g.get("genres", []))
        platforms = ", ".join(x["name"] for x in g.get("platforms", []))
        gid = g["id"]
        results.append({
            "igdb_id": gid,
            "title": g["name"],
            "cover_url": cover,
            "summary": g.get("summary", "")[:300] if g.get("summary") else "",
            "genres": genres,
            "platforms": platforms,
            "release_year": year,
            "rating": round(g["rating"] / 10, 1) if g.get("rating") else None,
            "match_score": tally.get(gid, 0),
            "because_of": source_names.get(gid, []),
        })

    results.sort(key=lambda x: (-x["match_score"], -(x["rating"] or 0)))
    return results


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
