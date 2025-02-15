import os
from pydantic_settings import BaseSettings

log_level = os.environ.get("LOG_LEVEL", "INFO")

def load_required_env_var(env_var_name: str) -> str:
    value = os.environ.get(env_var_name, "")
    if not value:
        raise ValueError(f"Missing required environment variable: {env_var_name}")
    return value

# Load required environment variables
bing_search_api_key = load_required_env_var("BING_SEARCH_API_KEY")

class Settings(BaseSettings):
    log_level: str = log_level
    bing_search_api_key: str = bing_search_api_key
    
