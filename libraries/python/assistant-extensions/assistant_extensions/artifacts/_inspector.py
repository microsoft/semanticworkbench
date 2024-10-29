#
# region Inspector
#

from typing import TYPE_CHECKING, Awaitable, Callable

from semantic_workbench_assistant.assistant_app import (
    AssistantContext,
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
)

if TYPE_CHECKING:
    from ._artifacts import ArtifactsExtension

from ._model import ArtifactsConfigModel


class ArtifactConversationInspectorStateProvider:
    display_name = "Artifacts"
    description = "Artifacts that have been co-created by the participants in the conversation. NOTE: This feature is experimental and disabled by default."

    def __init__(
        self,
        config_provider: Callable[[AssistantContext], Awaitable[ArtifactsConfigModel]],
        artifacts_extension: "ArtifactsExtension",
    ) -> None:
        self.config_provider = config_provider
        self.artifacts_extension = artifacts_extension

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """
        Get the artifacts for the conversation.
        """

        # get the configuration for the artifacts extension
        config = await self.config_provider(context.assistant)
        if not config.enabled:
            return AssistantConversationInspectorStateDataModel(
                data={"content": "Artifacts are disabled in assistant configuration."}
            )

        # get the artifacts for the conversation
        artifacts = self.artifacts_extension.get_all_artifacts(context)

        if not artifacts:
            return AssistantConversationInspectorStateDataModel(data={"content": "No artifacts available."})

        # create the data model for the artifacts
        data_model = AssistantConversationInspectorStateDataModel(
            data={"artifacts": [artifact.model_dump(mode="json") for artifact in artifacts]}
        )

        return data_model


# endregion
