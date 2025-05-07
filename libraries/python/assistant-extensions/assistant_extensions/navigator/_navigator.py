from typing import Any

navigator_metadata_key = "_assistant_navigator"


def metadata_for_assistant_navigator(metadata_for_navigator: dict[str, str]) -> dict[str, Any]:
    return {
        navigator_metadata_key: metadata_for_navigator,
    }


def extract_metadata_for_assistant_navigator(assistant_metadata: dict[str, Any]) -> dict[str, str] | None:
    return assistant_metadata.get(navigator_metadata_key)
