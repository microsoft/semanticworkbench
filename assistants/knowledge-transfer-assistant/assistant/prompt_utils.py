import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

import openai_client
from assistant_extensions.attachments import (
    AttachmentsConfigModel,
    AttachmentsExtension,
)
from openai.types.chat import (
    ChatCompletionMessageParam,
)
from pydantic import BaseModel, Field
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
)

from assistant.agentic import get_coordinator_next_action_suggestion
from assistant.data import (
    ConversationRole,
    CoordinatorConversationMessage,
    RequestStatus,
)
from assistant.domain.learning_objectives_manager import LearningObjectivesManager
from assistant.domain.share_manager import ShareManager
from assistant.domain.tasks_manager import TasksManager
from assistant.ui_tabs.common import get_priority_emoji, get_status_emoji


def create_system_message(content: str, delimiter: str | None = None) -> ChatCompletionMessageParam:
    if delimiter:
        delimiter = delimiter.strip().upper().replace(" ", "_")
        content = f"<{delimiter}>\n{content}\n</{delimiter}>"

    message: ChatCompletionMessageParam = {
        "role": "system",
        "content": content,
    }
    return message


class Instructions:
    """
    A class to represent a section of a prompt.
    """

    def __init__(
        self,
        content: str,
        title: str | None = None,
    ) -> None:
        self.title = title
        self.content = content
        self.level = 0
        self.subsections: list[Instructions] = []

    def add_subsection(self, subsection: "Instructions") -> None:
        """
        Add a subsection to the prompt section.
        """
        subsection.level = self.level + 1
        self.subsections.append(subsection)

    def __str__(self) -> str:
        s = ""
        if self.title:
            hashes = "#" * (self.level + 1)
            s += f"{hashes} {self.title}\n\n"
        s += self.content
        if self.subsections:
            s += "\n\n" + "\n\n".join(str(subsection) for subsection in self.subsections)

        return s


class Context(Protocol):
    def message(self) -> ChatCompletionMessageParam:
        raise NotImplementedError

    def content(self) -> str:
        raise NotImplementedError

    def name(self) -> str:
        raise NotImplementedError


class ChatCompletionMessageContext(Context):
    def __init__(self, message: ChatCompletionMessageParam, name: str | None) -> None:
        self._message = message
        self._name = name or "Attachment"

    def message(self) -> ChatCompletionMessageParam:
        return self._message

    def content(self) -> str:
        return f"<{self._name}>\n{self._message.get('content')}\n</{self._name}>"

    def name(self) -> str:
        return self._name


class DataContext(Context):
    def __init__(self, name: str, data: str, description: str | None = None) -> None:
        self._name = name
        self.description = description
        self.data = data

    def message(self) -> ChatCompletionMessageParam:
        return create_system_message(self.content(), self._name)

    def content(self) -> str:
        s = self.data
        if self.description:
            s = f"{self.description}\n\n'''\n{self.data}\n'''"
        return s

    def name(self) -> str:
        return self._name


class ContextStrategy(Enum):
    SINGLE = "single"  # Put all context chunks in a single message.
    MULTI = "multi"  # Put each context chunk in its own message.


@dataclass
class Prompt:
    instructions: Instructions
    output_format: str | None = None
    reasoning_steps: str | None = None
    examples: str | None = None
    contexts: list[Context] = field(default_factory=list)
    context_strategy: ContextStrategy = ContextStrategy.SINGLE
    final_instructions: str | None = None

    def messages(self) -> list[ChatCompletionMessageParam]:
        parts = [
            str(self.instructions),
        ]
        if self.reasoning_steps:
            parts.append("# Reasoning Steps")
            parts.append(self.reasoning_steps)
        if self.output_format:
            parts.append("# Output Format")
            parts.append(self.output_format)
        if self.examples:
            parts.append("# Examples")
            parts.append(self.examples)
        if self.contexts and self.context_strategy == ContextStrategy.SINGLE:
            parts.append("# Context")
            for context in self.contexts:
                parts.append(f"## {context.name()}")
                parts.append(context.content())
        s = "\n\n".join(parts)
        if self.final_instructions:
            s += "\n\n" + self.final_instructions

        messages = [
            create_system_message(s),
        ]

        if self.contexts and self.context_strategy == ContextStrategy.MULTI:
            for context in self.contexts:
                messages.append(context.message())

        return messages


class TokenBudget:
    def __init__(self, budget: int) -> None:
        self.budget = budget
        self.used = 0

    def add(self, tokens: int) -> None:
        self.used += tokens

    def remaining(self) -> int:
        return self.budget - self.used

    def is_under_budget(self) -> bool:
        return self.remaining() > 0

    def is_over_budget(self) -> bool:
        return self.remaining() < 0

    def fits(self, tokens: int) -> bool:
        return self.remaining() >= tokens


class ContextSection(Enum):
    """
    Enum to represent different sections of the conversation context.
    """

    KNOWLEDGE_INFO = "knowledge_info"
    KNOWLEDGE_BRIEF = "knowledge_brief"
    TARGET_AUDIENCE = "target_audience"
    LEARNING_OBJECTIVES = "learning_objectives"
    KNOWLEDGE_DIGEST = "knowledge_digest"
    INFORMATION_REQUESTS = "information_requests"
    SUGGESTED_NEXT_ACTIONS = "suggested_next_actions"
    COORDINATOR_CONVERSATION = "coordinator_conversation"
    ATTACHMENTS = "attachments"
    TASKS = "tasks"


async def add_context_to_prompt(
    prompt: Prompt,
    context: ConversationContext,
    role: ConversationRole,
    model: str,
    token_limit: int,
    attachments_extension: AttachmentsExtension | None = None,
    attachments_config: AttachmentsConfigModel | None = None,
    attachments_in_system_message: bool = False,
    include: list[ContextSection] | None = None,
) -> None:
    if include is None:
        return

    share = await ShareManager.get_share(context)

    if ContextSection.TASKS in include:
        tasks = await TasksManager.get_tasks(context)
        if tasks:
            tasks_data = json.dumps([task.model_dump() for task in tasks])
            prompt.contexts.append(
                DataContext(
                    "Task List",
                    tasks_data,
                )
            )

    if ContextSection.KNOWLEDGE_INFO in include:
        share_info_text = share.model_dump_json(
            indent=2,
            exclude={
                "brief",
                "learning_objectives",
                "audience_takeaways",
                "preferred_communication_style",
                "digest",
                "next_learning_actions",
                "requests",
                "tasks",
                "log",
            },
        )
        prompt.contexts.append(DataContext("Knowledge Share Info", share_info_text))

    if ContextSection.KNOWLEDGE_BRIEF in include and share and share.brief:
        brief_text = ""
        brief_text = f"**Title:** {share.brief.title}\n**Description:** {share.brief.content}"
        prompt.contexts.append(
            DataContext(
                "Knowledge Brief",
                brief_text,
            )
        )

    if ContextSection.TARGET_AUDIENCE in include and role == ConversationRole.COORDINATOR and share:
        if share.audience:
            audience_context = share.audience

            if share.audience_takeaways:
                audience_context += "\n\n**Intended takeaways for this audience:**\n"
                audience_context += "\n".join(f"- {takeaway}" for takeaway in share.audience_takeaways)
            else:
                audience_context += "\n\n**Note:** No specific takeaways defined for this audience. Please define them to help guide the knowledge transfer process."  # noqa: E501

            if not share.is_intended_to_accomplish_outcomes:
                audience_context += "\n\n**Note:** This knowledge package is intended for general exploration, not specific learning outcomes."  # noqa: E501
        else:
            audience_context = "The intended audience for this knowledge transfer has not been defined yet. Please define it to help guide the knowledge transfer process."  # noqa: E501

        prompt.contexts.append(
            DataContext(
                "Target Audience",
                audience_context,
            )
        )

    # Learning objectives
    if ContextSection.LEARNING_OBJECTIVES in include and share and share.learning_objectives:
        learning_objectives_text = ""
        conversation_id = str(context.id)

        # Show progress based on role
        if role == ConversationRole.COORDINATOR:
            # Coordinator sees overall progress across all team members
            achieved_overall, total_overall = LearningObjectivesManager.get_overall_completion(share)
            learning_objectives_text += (
                f"Overall Progress: {achieved_overall}/{total_overall} outcomes achieved by team members\n\n"
            )
        else:
            # Team member sees their personal progress
            if conversation_id in share.team_conversations:
                achieved_personal, total_personal = LearningObjectivesManager.get_completion_for_conversation(
                    share, conversation_id
                )
                progress_pct = int(achieved_personal / total_personal * 100) if total_personal > 0 else 0
                learning_objectives_text += (
                    f"My Progress: {achieved_personal}/{total_personal} outcomes achieved ({progress_pct}%)\n\n"
                )

        learning_objectives = {}
        for objective in share.learning_objectives:
            learning_objectives[objective.id] = objective.model_dump()
        learning_objectives_text = json.dumps(
            learning_objectives,
            indent=2,
        )

        prompt.contexts.append(
            DataContext(
                "Learning Objectives",
                learning_objectives_text,
            )
        )

    if ContextSection.KNOWLEDGE_DIGEST in include and share and share.digest and share.digest.content:
        prompt.contexts.append(
            DataContext(
                "Knowledge digest",
                share.digest.content,
                "The assistant-maintained knowledge digest.",
            )
        )

    if ContextSection.INFORMATION_REQUESTS in include and share:
        all_requests = share.requests
        if role == ConversationRole.COORDINATOR:
            active_requests = [r for r in all_requests if r.status != RequestStatus.RESOLVED]
            if active_requests:
                coordinator_requests = (
                    "> 📋 **Use the request ID (not the title) with resolve_information_request()**\n\n"
                )
                for req in active_requests[:10]:  # Limit to 10 for brevity
                    priority_emoji = get_priority_emoji(req.priority)
                    status_emoji = get_status_emoji(req.status)
                    coordinator_requests += f"{priority_emoji} **{req.title}** {status_emoji}\n"
                    coordinator_requests += f"   **Request ID:** `{req.request_id}`\n"
                    coordinator_requests += f"   **Description:** {req.description}\n\n"

                if len(active_requests) > 10:
                    coordinator_requests += f"*...and {len(active_requests) - 10} more requests.*\n"
            else:
                coordinator_requests = "No active information requests."
            prompt.contexts.append(
                DataContext(
                    "Information Requests",
                    coordinator_requests,
                )
            )
        else:  # team role
            information_requests_info = ""
            my_requests = []

            # Filter for requests from this conversation that aren't resolved.
            my_requests = [
                r for r in all_requests if r.conversation_id == str(context.id) and r.status != RequestStatus.RESOLVED
            ]

            if my_requests:
                information_requests_info = ""
                for req in my_requests:
                    information_requests_info += (
                        f"- **{req.title}** (ID: `{req.request_id}`, Priority: {req.priority})\n"
                    )
            else:
                information_requests_info = "No active information requests."

            prompt.contexts.append(
                DataContext(
                    "Information Requests",
                    information_requests_info,
                )
            )

    if ContextSection.SUGGESTED_NEXT_ACTIONS in include and share and role == ConversationRole.COORDINATOR:
        next_action_suggestion = await get_coordinator_next_action_suggestion(context)
        if next_action_suggestion:
            prompt.contexts.append(
                DataContext(
                    "Suggested Next Actions",
                    next_action_suggestion,
                    "Actions the coordinator should consider taking based on the current knowledge transfer state.",
                )
            )

    # Figure out the token budget so far.
    token_budget = TokenBudget(token_limit)
    token_budget.add(
        openai_client.num_tokens_from_messages(
            model=model,
            messages=prompt.messages(),
        )
    )

    # Coordinator conversation
    if ContextSection.COORDINATOR_CONVERSATION in include:
        coordinator_conversation = await ShareManager.get_coordinator_conversation(context)
        if coordinator_conversation:
            # Limit messages to the configured max token count.
            total_coordinator_conversation_tokens = 0
            selected_coordinator_conversation_messages: list[CoordinatorConversationMessage] = []
            for msg in reversed(coordinator_conversation.messages):
                tokens = openai_client.num_tokens_from_string(msg.model_dump_json(), model=model)
                if total_coordinator_conversation_tokens + tokens > token_limit:
                    break
                selected_coordinator_conversation_messages.append(msg)
                total_coordinator_conversation_tokens += tokens

            class CoordinatorMessageList(BaseModel):
                messages: list[CoordinatorConversationMessage] = Field(default_factory=list)

            selected_coordinator_conversation_messages.reverse()
            coordinator_message_list = CoordinatorMessageList(messages=selected_coordinator_conversation_messages)
            coordinator_message_list_data = coordinator_message_list.model_dump_json()

            if attachments_in_system_message:
                prompt.contexts.append(
                    DataContext(
                        "Message History",
                        coordinator_message_list_data,
                    )
                )
            else:
                coordinator_message_list_data = (
                    f"<COORDINATOR_CONVERSATION>{coordinator_message_list_data}</COORDINATOR_CONVERSATION>"
                )
                prompt.contexts.append(DataContext("Attachment", coordinator_message_list_data))

            # TODO: To get exact token count, we should add delimiters.
            token_budget.add(
                openai_client.num_tokens_from_string(
                    model=model,
                    string=coordinator_message_list_data,
                )
            )

    # Attachments
    if ContextSection.ATTACHMENTS in include and share and attachments_config and attachments_extension:
        # Generate the attachment messages.
        # TODO: This will exceed the token limit if there are too many attachments.

        attachment_messages: list[ChatCompletionMessageParam] = openai_client.convert_from_completion_messages(
            await attachments_extension.get_completion_messages_for_attachments(
                context,
                config=attachments_config,
            )
        )

        if attachments_in_system_message:
            attachments_data = "\n\n".join(f"{msg['content']}" for msg in attachment_messages if "content" in msg)
            prompt.contexts.append(
                DataContext(
                    "Attachments",
                    attachments_data,
                    "The attachments provided by the user.",
                )
            )
            # TODO: To get exact token count, we should add delimiters.
            token_budget.add(
                openai_client.num_tokens_from_string(
                    model=model,
                    string=attachments_data,
                )
            )

        else:
            for a in attachment_messages:
                prompt.contexts.append(
                    ChatCompletionMessageContext(
                        name="Attachment",
                        message=a,
                    )
                )
            token_budget.add(
                openai_client.num_tokens_from_messages(
                    model=model,
                    messages=attachment_messages,
                )
            )
