from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    DIR_PATH_DOWNLOAD: str = './text'



settings = Settings()
