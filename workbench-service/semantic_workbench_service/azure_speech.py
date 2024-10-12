from azure.identity import DefaultAzureCredential

from . import settings


def get_token() -> dict[str, str]:
    credential = DefaultAzureCredential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    return {"token": token.token}


def get_service_access() -> dict[str, str]:
    if settings.azure_speech.resource_id == "" or settings.azure_speech.region == "":
        return {}

    return {
        "token": f"aad#{settings.azure_speech.resource_id}#{get_token()['token']}",
        "region": settings.azure_speech.region,
    }
