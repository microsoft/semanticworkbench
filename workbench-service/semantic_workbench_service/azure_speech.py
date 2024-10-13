from azure.identity import DefaultAzureCredential

from . import settings


def get_token() -> dict[str, str]:
    if settings.azure_speech.resource_id == "" or settings.azure_speech.region == "":
        return {}

    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default").token

    return {
        "token": f"aad#{settings.azure_speech.resource_id}#{token}",
        "region": settings.azure_speech.region,
    }
