import os

import pytest
from openai_client import AzureOpenAIAzureIdentityAuthConfig, AzureOpenAIServiceConfig, create_client
from pydantic import HttpUrl
from skill_library.types import LanguageModel


@pytest.fixture
def client() -> LanguageModel:
    azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    if not azure_openai_endpoint or not azure_openai_deployment:
        # FIXME: Paul, make sure this is in your environment.
        azure_openai_endpoint = "https://lightspeed-team-shared-openai-eastus.openai.azure.com/"
        azure_openai_deployment = "gpt-4o"
        # pytest.skip("AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_DEPLOYMENT must be available in the environment.")

    service_config = AzureOpenAIServiceConfig(
        auth_config=AzureOpenAIAzureIdentityAuthConfig(),
        azure_openai_endpoint=HttpUrl(azure_openai_endpoint),
        azure_openai_deployment=azure_openai_deployment,
    )
    return create_client(service_config)
