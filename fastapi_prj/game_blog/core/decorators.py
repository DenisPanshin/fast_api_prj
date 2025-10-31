from functools import wraps

from fastapi.responses import RedirectResponse
from fastapi.requests import Request
from sqlalchemy.orm import Session

from apps.authapp.utils import get_user_by_token


def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get('request')
        token = request.cookies.get('token')
        db: Session = kwargs.get('db')

        if request is None or token is None or not await get_user_by_token(token, db):
            return RedirectResponse('/login')

        return await func(*args, **kwargs)

    return wrapper
