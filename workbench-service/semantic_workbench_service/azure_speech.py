import logging

from azure.identity import DefaultAzureCredential

from . import settings

logger = logging.getLogger(__name__)


def get_token() -> dict[str, str]:
    if settings.azure_speech.resource_id == "" or settings.azure_speech.region == "":
        return {}

    credential = DefaultAzureCredential()
    try:
        token = credential.get_token("https://cognitiveservices.azure.com/.default").token
    except Exception as e:
        logger.error(f"Failed to get token: {e}")
        return {}

    return {
        "token": f"aad#{settings.azure_speech.resource_id}#{token}",
        "region": settings.azure_speech.region,
    }
