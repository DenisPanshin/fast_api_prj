from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from apps.authapp.routes import user_router
from apps.authapp.utils import get_current_user

from core.config import TemplateResponse
from core.decorators import login_required
from core.requests_framework import setup_user_dict
from db.session import get_db
from apps.postapp.routes import post_route

api_router = APIRouter()
api_router.include_router(user_router)
api_router.include_router(post_route)


@api_router.get("/", response_class=HTMLResponse)
@api_router.post("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    request.name = 'home'
    response_dict = await setup_user_dict(request, db)
    return TemplateResponse('index.jinja2', response_dict)
