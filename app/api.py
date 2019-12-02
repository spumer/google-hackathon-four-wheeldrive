import firebase_admin
import pydantic
from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from starlette.status import HTTP_401_UNAUTHORIZED

from app import models
from app.tochka_auth import authenticate_user
from app.tochka_auth import get_authorize_url

app = FastAPI()
firebase_app = firebase_admin.initialize_app()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/oauth')


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


class Token(BaseModel):
    token: bytes


class TokenData(BaseModel):
    username: str
    email: pydantic.EmailStr
    # Любчая часть ФИО может отсутствовать
    first_name: str = None
    last_name: str = None
    patronymic: str = None


class OAuth2RedirectQuery:
    """This is a dependency class, use it like:

        @app.post("/token")
        def token(form_data: OAuth2RedirectQuery = Depends()):
            data = form_data.parse()
            print(data.code)
            print(data.redirect_uri)
            return data
    """

    def __init__(
        self,
        code: str = Query(...),
        redirect_uri: pydantic.AnyUrl = Query(''),
    ):
        self.code = code
        self.redirect_uri = redirect_uri


@app.post('/auth/obtain-token', response_model=Token, tags=['auth'])
async def redirect_for_jwt_token(data: OAuth2RedirectQuery = Depends()):
    user, data = await authenticate_user(data.code, data.redirect_uri)
    token = auth.create_custom_token(user.username)
    return Token(token=token)


@app.get('/auth/redirect', tags=['auth'], name='auth_redirect')
async def redirect_to_auth():
    return RedirectResponse(get_authorize_url())


def get_user(token_data: TokenData) -> models.User:
    try:
        user = models.User.get_exact(username=token_data.username)
    except models.User.DoesNotExist:
        user = models.User.create(**token_data.dict())

    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = auth.verify_id_token(token)
    except (
        ValueError, auth.InvalidIdTokenError, auth.ExpiredIdTokenError,
        auth.RevokedIdTokenError, auth.CertificateFetchError,
    ):
        raise credentials_exception

    user_data: dict = payload.get('user_data')
    if user_data is None:
        raise credentials_exception

    token_data = TokenData(**user_data)
    user = get_user(token_data)

    if user is None:
        raise credentials_exception

    return user


@app.post('/api/v1/enqueue')
def add_me_to_meeting_queue(current_user: models.User = Depends(get_current_user)):
    models.WaitMeetingQueue.insert(user=current_user).on_conflict_ignore()
    return None


@app.post('/api/v1/unenqueue')
def remove_me_from_meeting_queue(current_user: models.User = Depends(get_current_user)):
    models.WaitMeetingQueue.filter(user=current_user).delete()
    return None


@app.get('/')
async def read_root():
    return RedirectResponse(app.url_path_for('docs'))
