from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    log_level: str = "INFO"
    giphy_api_key: str = ""


settings = Settings()
