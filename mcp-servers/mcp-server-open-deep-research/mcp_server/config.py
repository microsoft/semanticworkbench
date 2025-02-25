import os
import dotenv

from pydantic_settings import BaseSettings

# Load environment variables from .env file
dotenv.load_dotenv()

data_folder = os.environ.get("DATA_FOLDER", ".data")
log_level = os.environ.get("LOG_LEVEL", "INFO")


def load_required_env_var(env_var_name: str) -> str:
    value = os.environ.get(env_var_name, "")
    if not value:
        raise ValueError(f"Missing required environment variable: {env_var_name}")
    return value


huggingface_token = load_required_env_var("HUGGINGFACE_TOKEN")
openai_api_key = load_required_env_var("OPENAI_API_KEY")
serpapi_api_key = load_required_env_var("SERPAPI_API_KEY")


class Settings(BaseSettings):
    data_folder: str = data_folder
    log_level: str = log_level
    huggingface_token: str = huggingface_token
    openai_api_key: str = openai_api_key
    serpapi_api_key: str = serpapi_api_key
