from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import uvicorn

from app.database import init_db
from app.routers import auth, games, votes, recommendations
from app.dependencies import get_current_user_optional


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="GameBackLoggarr", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
app.include_router(games.router)
app.include_router(votes.router)
app.include_router(recommendations.router)



@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse("/login", status_code=302)
    return RedirectResponse("/games", status_code=302)
