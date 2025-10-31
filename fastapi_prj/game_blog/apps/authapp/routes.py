from fastapi import APIRouter
from fastapi.requests import Request
from fastapi import Depends
from sqlalchemy.orm import Session

from apps.authapp.schemas import UserCreate
from core.config import TemplateResponse
from db.session import get_db
from fastapi import responses
from .models import Token, User

from apps.authapp.form import UserUpdateForm
from sqlalchemy.exc import IntegrityError

from .utils import get_user_by_email, create_user, validate_password, \
    create_user_token, send_message, do_hash_password

user_router = APIRouter()


@user_router.post('/register/')
@user_router.get('/register/')
async def register(request: Request, db: Session = Depends(get_db)):
    request.name = 'register'
    if request.method == 'GET':
        return TemplateResponse("auth/register.jinja2", {"request": request})
    else:
        form = await request.form()
        form_register_data = {
            'username': form.get('username'),
            'email': form.get('email'),
            'password': form.get('password'),
        }
        user = UserCreate(**form_register_data)
        db_user = await get_user_by_email(email=user.email, db=db)
        if db_user:
            return TemplateResponse("auth/register.jinja2",
                                    {"request": request,
                                     "error": 'User with this email has already'})
        else:
            new_user = await create_user(user, db)
            response = responses.RedirectResponse('/login/')
            response.set_cookie('logged', 'true')
            return response


@user_router.post('/update/')
@user_router.get('/update/')
async def update(request: Request, db: Session = Depends(get_db)):
    if request.method == 'GET':
        return TemplateResponse("auth/update.html", {"request": request})
    else:
        form = UserUpdateForm(request)
        await form.load_data()
        if await form.is_valid(db):
            try:
                user = db.query(User).filter(
                    User.username == form.old_name).first()
                if form.username:
                    user.username = form.username
                if form.email:
                    user.email = form.email
                db.commit()
                return responses.JSONResponse(
                    {'status': 'success', 'user': user.username})
            except IntegrityError:
                form.__dict__.get("errors").append(
                    "Duplicate username or email")
                return TemplateResponse("auth/update.html", form.__dict__)

        return TemplateResponse("auth/update.html", form.__dict__)


@user_router.post('/login/')
@user_router.get('/login/')
async def login_page(request: Request, db: Session = Depends(get_db)):
    request.name = 'login'
    is_logged = request.cookies.get('logged')

    if request.method == "POST" and is_logged:
        response = TemplateResponse('auth/login.jinja2', {'request': request},
                                    headers=None)
        response.delete_cookie('logged')
        return response

    if request.method == 'GET':
        return TemplateResponse('auth/login.jinja2', {'request': request})
    form = await request.form()

    user = await get_user_by_email(form.get('email'), db)

    if not user or not validate_password(password=form.get('password'),
                                         hashed_password=user.hashed_password):
        return TemplateResponse('auth/login.jinja2', {'request': request,
                                                      'error': 'Incorrect email or password'})

    response = responses.RedirectResponse('/?msg=Successfully-Logged')

    token = await create_user_token(user.uid, db)
    response.set_cookie('token', token.token)
    return response


@user_router.get('/logout/')
async def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get('token')
    token_db = db.query(Token).filter(Token.token == token).first()
    db.delete(token_db)
    db.commit()
    response = responses.RedirectResponse('/')
    response.delete_cookie('token')
    return response


@user_router.get('/reset_password/')
@user_router.post('/reset_password/')
async def reset_password(request: Request, db: Session = Depends(get_db)):
    context = {'request': request}

    if request.method == 'POST':
        form = await request.form()
        email = form.get('email')
        user: User = await get_user_by_email(email, db)
        if not user:
            context['error'] = f'user with email: {email} not register'
        else:
            token = user.get_reset_token()
            print(token)

            await send_message(request.url_for('change_password', token=token),
                               user)

            context[
                'success'] = f'SUCCESS!!! Instruction for reset password was sending on your email'

    return TemplateResponse('auth/reset_password.jinja2', context)


@user_router.get('/change_password/{token}')
@user_router.post('/change_password/{token}')
async def change_password(token: str, request: Request,
                          db: Session = Depends(get_db)):
    context = {'request': request}
    token = token.encode('utf-8')

    payload = User.get_payload_from_reset_token(token)
    if request.method == 'POST' and payload:

        form = await request.form()

        password = form.get('password')
        confirm_password = form.get('confirm_password')

        if password and password != confirm_password:
            context['error'] = 'Пароли не совпадают или вы ничего не ввели'

        else:
            user = db.query(User).filter(
                User.uid == payload['user_uid']).first()
            if not user:
                context['error'] = 'Возникла неизвестная ошибка'
            else:
                user.hashed_password = await do_hash_password(password)
                db.commit()
                context[
                    'success'] = 'Пароль успешно изменен, можете попробовать по нему зайти'

    return TemplateResponse('auth/change_password.jinja2', context)
