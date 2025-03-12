from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = "INFO"
    data_folder: str = ".data"
    azure_openai_endpoint: str = "gpt-4o"
    azure_openai_deployment: str = ""
    azure_openai_reasoning_deployment: str = "o1-mini"
    bing_subscription_key: str = ""
    bing_search_url: str = "https://api.bing.microsoft.com/v7.0/search"
    serpapi_api_key: str = ""
    huggingface_token: str = ""


settings = Settings()

def ensure_required_settings() -> None:
    # Ensure required settings are set.
    # These values should have been set in the environment.
    required_settings = ["azure_openai_deployment", "azure_openai_endpoint", "bing_subscription_key"]
    missing_settings = [setting for setting in required_settings if not getattr(settings, setting)]

    if missing_settings:
        raise ValueError(f"Missing required settings: {', '.join(missing_settings)}")
