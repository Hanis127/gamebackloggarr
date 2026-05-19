# 🎮 Backloggarr

A self-hosted co-op game backlog manager for two people. Suggest games, vote on what to play next, and track your progress — with automatic metadata from IGDB (cover art, description, genres, platforms, ratings).

## Features

- **Multi-user auth** — two accounts, invite-code protected registration
- **IGDB search** — type a game name, pick from live autocomplete with cover art
- **Auto metadata** — cover, summary, genres, platforms, release year, IGDB rating
- **Voting** — upvote / downvote per game, sorted by score
- **Status tracking** — Backlog → Playing → Completed → Dropped
- **Single Docker container**, SQLite database (no extra services)

## Quick Start

### 1. Get IGDB credentials (free)

1. Go to [dev.twitch.tv/console](https://dev.twitch.tv/console)
2. Sign in with a Twitch account (or create one — it's free)
3. Click **Register Your Application**
4. Name: anything (e.g. `backloggarr`), OAuth Redirect URL: `http://localhost`, Category: `Application Integration`
5. Copy your **Client ID** and generate a **Client Secret**

### 2. Configure

Edit `docker-compose.yml` and fill in:

```yaml
IGDB_CLIENT_ID: "your_client_id_here"
IGDB_CLIENT_SECRET: "your_client_secret_here"
INVITE_CODE: "pick-a-secret-word"
```

### 3. Run

```bash
docker compose up -d
```

Then open [http://localhost:8000](http://localhost:8000).

### 4. Create accounts

1. Go to `/register`
2. Enter a username, password, and the invite code you set
3. Share the invite code with your co-op partner so they can register too

---

## Usage

| Action | How |
|--------|-----|
| Suggest a game | Click **+ Suggest a Game**, type in search box, pick from results |
| Vote | ▲ / ▼ buttons on each card — click again to undo |
| Change status | Dropdown on each card (Backlog / Playing / Completed / Dropped) |
| Remove a game | ✕ button on the card |
| Sort | Votes / Newest / Title / Rating bar above the grid |

## Without IGDB credentials

The app still works — you just won't get the search autocomplete or metadata. The IGDB search endpoint will return empty results. You can still add games manually by extending the add form if needed.

## Development

```bash
pip install -r requirements.txt
export IGDB_CLIENT_ID=xxx IGDB_CLIENT_SECRET=yyy INVITE_CODE=dev DB_PATH=./data/backloggarr.db
uvicorn app.main:app --reload
```

## Stack

- **Backend:** FastAPI + Python 3.12
- **Templating:** Jinja2 (server-rendered HTML)
- **Database:** SQLite (WAL mode)
- **Metadata:** [IGDB API v4](https://api-docs.igdb.com/)
- **Fonts:** Syne + DM Mono
