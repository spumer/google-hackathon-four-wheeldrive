import os
import sys
import typing

import dotenv
import pydantic
from pydantic import BaseSettings
from pydantic import PostgresDsn
from pydantic import SecretStr

if sys.platform.startswith('linux'):
    tmp_path = '/dev/shm'
else:
    # on MacOS /dev/shm not available
    tmp_path = '.'

# FIXME: workaround (part1) for google credential loading mechanism
GOOGLE_APPLICATION_CREDENTIALS_PATH: str = f'{tmp_path}/GOOGLE_APPLICATION_CREDENTIALS'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_APPLICATION_CREDENTIALS_PATH


class Config(BaseSettings):
    DATABASE_URL: PostgresDsn
    DB_HOST: typing.Optional[str] = None
    DB_PORT: typing.Optional[int] = None
    DB_USER: typing.Optional[str] = None
    DB_PASSWORD: typing.Optional[str] = None
    DB_NAME: typing.Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS_CONTENT: SecretStr
    GOOGLE_APPLICATION_CREDENTIALS: str
    OAUTH_CLIENT_ID: str = 'e3e4eb9c'
    OAUTH_CLIENT_SECRET: SecretStr
    OAUTH_REDIRECT_URI: str = 'https://tochka-coffee.firebaseapp.com/authorization/oauth'

    @pydantic.validator('DB_HOST', pre=True)
    def populate_db_host(cls, v, values, **kwargs):
        url: PostgresDsn = values['DATABASE_URL']
        return url.host

    @pydantic.validator('DB_PORT', pre=True)
    def populate_db_port(cls, v, values, **kwargs):
        url: PostgresDsn = values['DATABASE_URL']
        return url.port

    @pydantic.validator('DB_PASSWORD', pre=True)
    def populate_db_password(cls, v, values, **kwargs):
        url: PostgresDsn = values['DATABASE_URL']
        return url.password

    @pydantic.validator('DB_NAME', pre=True)
    def populate_db_name(cls, v, values, **kwargs):
        url: PostgresDsn = values['DATABASE_URL']
        return url.path


dotenv.load_dotenv()
config = Config()

# FIXME: workaround (part2) for google credential loading mechanism
with open(config.GOOGLE_APPLICATION_CREDENTIALS, 'w') as fp:
    fp.write(config.GOOGLE_APPLICATION_CREDENTIALS_CONTENT.get_secret_value())
