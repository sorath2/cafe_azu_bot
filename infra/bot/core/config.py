import os

from pydantic import Field
from pydantic_settings import BaseSettings

RUNNING_IN_DOCKER = os.getenv('IS_DOCKER', False) == 'DOCKER'


class EnvSet(BaseSettings):
    class Config:
        env_file = None if RUNNING_IN_DOCKER else '../infra/config/.general'
        extra = 'ignore'


class Settings(EnvSet):
    bot_token: str
    db_name: str = Field(alias='POSTGRES_DB')
    host: str = Field(alias='POSTGRES_HOST')
    port: int = Field(alias='POSTGRES_PORT')
    user: str = Field(alias='POSTGRES_USER')
    password: str = Field(alias='POSTGRES_PASSWORD')
    merchant_login: str
    merchant_password1: str
    merchant_password2: str
    payment_timeout: int
    test_mode: bool

    @property
    def database_url(self):
        # DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB_NAME
        host = self.host if RUNNING_IN_DOCKER else 'localhost'
        return (
            f'postgresql+asyncpg://{self.user}:{self.password}@'
            f'{host}:{self.port}/{self.db_name}'
        )


settings = Settings()
