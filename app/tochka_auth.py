import typing

import aioauth_client
from fastapi import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

from app.config import config


class TochkaClient(aioauth_client.OAuth2Client):
    authorize_url = 'https://auth.tochka-tech.com/authorize'
    access_token_url = 'https://auth.tochka-tech.com/token'
    user_info_url = 'https://auth.tochka-tech.com/who'
    name = 'tochka'
    base_url = 'https://auth.tochka-tech.com'

    def user_parse(self, data):
        """Parse information from the provider."""
        user = data['user']
        username = user['username'].lower()
        yield 'username', username
        yield 'email', user['email'].lower()
        yield 'first_name', user.get('name')
        yield 'last_name', user.get('surname')
        yield 'patronymic', user.get('patronymic')
        yield 'picture', f'{self._get_url("photo")}/{username}'


fake_users_db = {
    'johndoe': {
        'username': 'johndoe',
        'full_name': 'John Doe',
        'email': 'johndoe@example.com',
        'hashed_password': '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
        'disabled': False,
    },
}


tochka = TochkaClient(
    client_id=config.OAUTH_CLIENT_ID,
    client_secret=config.OAUTH_CLIENT_SECRET.get_secret_value(),
)


def get_authorize_url():
    return tochka.get_authorize_url(scope='default', redirect_uri='http://localhost:8000/auth/oauth')


async def authenticate_user(code, redirect_uri=None) -> typing.Tuple[aioauth_client.User, dict]:
    if redirect_uri is None:
        redirect_uri = config.OAUTH_REDIRECT_URI

    try:
        token, _ = await tochka.get_access_token(code, redirect_uri=redirect_uri)
        user, data = await tochka.user_info(headers={'Authorization': f'Bearer {token}'})
    except Exception:
        # FIXME: catch valuable exceptions
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail='Auth failed',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    return user, data
