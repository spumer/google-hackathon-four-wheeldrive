import os
import sys

import dotenv
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
    GOOGLE_APPLICATION_CREDENTIALS_CONTENT: SecretStr
    GOOGLE_APPLICATION_CREDENTIALS: str
    OAUTH_CLIENT_ID: str = 'e3e4eb9c'
    OAUTH_CLIENT_SECRET: SecretStr


dotenv.load_dotenv()
config = Config()

# FIXME: workaround (part2) for google credential loading mechanism
with open(config.GOOGLE_APPLICATION_CREDENTIALS, 'w') as fp:
    fp.write(config.GOOGLE_APPLICATION_CREDENTIALS_CONTENT.get_secret_value())
