import firebase_admin
import pydantic
from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth
from pydantic import BaseModel
from starlette.responses import RedirectResponse
from starlette.status import HTTP_401_UNAUTHORIZED

from app.tochka_auth import authenticate_user
from app.tochka_auth import get_authorize_url

app = FastAPI()
firebase_app = firebase_admin.initialize_app()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/token')


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


@app.get('/auth/oauth', response_model=Token, tags=['auth'])
async def redirect_for_jwt_token(data: OAuth2RedirectQuery = Depends()):
    user, data = await authenticate_user(data.code, data.redirect_uri)
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    token = auth.create_custom_token(user.username)
    return Token(token=token)


@app.get('/auth/redirect', tags=['auth'], name='auth_redirect')
async def redirect_to_auth():
    return RedirectResponse(get_authorize_url())


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = auth.verify_id_token(token)
        user_data: dict = payload.get('user_data')
        if user_data is None:
            raise credentials_exception
        token_data = TokenData(**user_data)
    except (
        ValueError, auth.InvalidIdTokenError, auth.ExpiredIdTokenError,
        auth.RevokedIdTokenError, auth.CertificateFetchError,
    ):
        raise credentials_exception

    '''
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    '''
    return token_data


@app.get('/')
async def read_root():
    return RedirectResponse(app.url_path_for('auth_redirect'))
