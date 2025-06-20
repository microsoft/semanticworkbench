# Copyright (c) Microsoft. All rights reserved.

import asyncio
import io
import json
import logging
import random
import time

import pendulum
from assistant_drive import Drive, DriveConfig, IfDriveFileExistsBehavior
from liquid import render
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai_client import create_client
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
    storage_directory_for_context,
)

from assistant.config import AssistantConfigModel
from assistant.context_management.context_manager import complete_context_management
from assistant.context_management.conv_compaction import get_compaction_data
from assistant.context_management.inspector import ContextManagementInspector
from assistant.filesystem import AttachmentsExtension
from assistant.filesystem._tasks import get_filesystem_metadata
from assistant.response.utils.openai_utils import convert_oai_messages_to_xml, get_completion
from assistant.response.utils.tokens_tiktoken import TokenizerOpenAI
from assistant.types import FileManagerData, FileRelevance

logger = logging.getLogger(__name__)

USE_FAST_SCORING = True

FILE_SCORE_SYSTEM_PROMPT = """You are determining the probability of a file being relevant to the conversation and topics being discussed.
You will be provided with a conversation history and the content of the file to analyze. \
Note that sometimes the file content will actually be a chunk of a conversation. \
Additionally, the conversation history may contain other files, these are NOT the files you are scoring. \
Do not let these aspects confuse you. Use the XML tags to determine what is what.
From the conversation history, you should extrapolate what the the conversation is about to determine if a file is **core** \
to understanding the context of what is happening or if it is specific to one topic or question at a point in time.
Current date: {{current_datetime}}

1. Conduct brief reasoning
Ask yourself questions such as the following to determine the probability of the file being overall relevant to the next task the user might want:
- What is the likelihood that the file will be needed to complete the next task that the user will ask?
- Is the file something that has been added or used recently? For example, documents that the user has recently edited or added should be scored very highly.
- Is it a file that provides important global context? For example, guidelines, a framing document, goals, checklists, etc. If so that file should be scored the highest for relevance.
  - While these files might not be explictly used or referenced, but they contribute to the overall understanding and thus should be score higher for recency as well.
- Does the file have meaningful content or does it seem like more random notes or a draft? If so, that file is probably not as relevant.

2. Determine Recency Probability
- Based on the conversation, the file content, and your reasoning provide a score that indicates how recently the file has been leveraged.
- You should subtract 0.1 for every turn (where a turn starts with a user message and ends with the final assistant message) since the file was last used.

3. Determine Relevance Probability
- Similarly, based on the conversation, the file content, and your reasoning provide a score that indicates how \
relevant the file is to the next task the user might want to do and/or their overall goals
- Don't let the recency probability influence this score, rather focus on the content of the file and the conversation history."""

FILE_SCORE_USER_PROMPT = """{{conversation_history}}

<file_content path="{{file_path}}">
{{file_content}}
</file_content>

Now briefly reason and determine the recency and relevance probabilities."""


FILE_SCORE_SCHEMA = {
    "name": "score_file",
    "schema": {
        "type": "object",
        "properties": {
            "relevance_probability": {
                "type": "object",
                "properties": {
                    "brief_reasoning": {
                        "type": "string",
                        "description": "Your reasoning about the probability of the file's (near) future relevance to the user's next task and goals. Keep it to 100 words or less",
                    },
                    "recency_probability": {
                        "type": "number",
                        "description": "Probability (from 0 to 1) that the file is relevant to the user's next task based on how recently it has been used.",
                    },
                    "relevance_probability": {
                        "type": "number",
                        "description": "Probability (from 0 to 1) that the file is relevant to the user's next task based on its content and the conversation context.",
                    },
                },
                "required": [
                    "brief_reasoning",
                    "recency_probability",
                    "relevance_probability",
                ],
                "additionalProperties": False,
                "description": "Reasoning and probabilities for the file's relevance to the user's next task.",
            }
        },
        "required": ["relevance_probability"],
        "additionalProperties": False,
    },
    "strict": True,
}

MULTI_FILE_SCORE_SYSTEM_PROMPT = """You are determining the probability of files being relevant to the conversation and topics being discussed.
You will be provided with a conversation history and the summarized contents of files for analyze. \
Note that sometimes the file content will actually be a chunk of a conversation. \
Additionally, the conversation history may contain other files, these are NOT the files you are scoring. \
Do not let these aspects confuse you. Use the XML tags to determine what is what.
From the conversation history, you should extrapolate what the the conversation is about to determine if a file is **core** \
to understanding the context of what is happening or if it is specific to one topic or question at a point in time.
Current date: {{current_datetime}}

FOR EACH FILE:
1. Write down the file name/path

2. Conduct brief reasoning
Ask yourself questions such as the following to determine the probability of the file being overall relevant to the next task the user might want:
- What is the likelihood that the file will be needed to complete the next task that the user will ask?
- Is the file something that has been added or used recently? For example, documents that the user has recently edited or added should be scored very highly.
- Is it a file that provides important global context? For example, guidelines, a framing document, goals, checklists, etc. If so that file should be scored the highest for relevance.
  - While these files might not be explictly used or referenced, but they contribute to the overall understanding and thus should be score higher for recency as well.
- Does the file have meaningful content or does it seem like more random notes or a draft? If so, that file is probably not as relevant.

3. Determine Recency Probability
- Based on the conversation, the file content, and your reasoning provide a score that indicates how recently the file has been leveraged.
- You should subtract 0.1 for every turn (where a turn starts with a user message and ends with the final assistant message) since the file was last used.

4. Determine Relevance Probability
- Similarly, based on the conversation, the file content, and your reasoning provide a score that indicates how \
relevant the file is to the next task the user might want to do and/or their overall goals
- Don't let the recency probability influence this score, rather focus on the content of the file and the conversation history."""

MULTI_FILE_SCORE_USER_PROMPT = """{{conversation_history}}

<files_to_score>
{{files_content}}
</files_to_score>

Now briefly reason and determine the recency and relevance probabilities for each file."""

MULTI_FILE_SCORE_SCHEMA = {
    "name": "score_files",
    "schema": {
        "type": "object",
        "properties": {
            "file_scores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file_name": {
                            "type": "string",
                            "description": "The name/path of the file being scored",
                        },
                        "brief_reasoning": {
                            "type": "string",
                            "description": "Your reasoning about the probability of the file's (near) future relevance to the user's next task and goals. Keep it to 100 words or less",
                        },
                        "recency_probability": {
                            "type": "number",
                            "description": "Probability (from 0 to 1) that the file is relevant to the user's next task based on how recently it has been used.",
                        },
                        "relevance_probability": {
                            "type": "number",
                            "description": "Probability (from 0 to 1) that the file is relevant to the user's next task based on its content and the conversation context.",
                        },
                    },
                    "required": [
                        "file_name",
                        "brief_reasoning",
                        "recency_probability",
                        "relevance_probability",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["file_scores"],
        "additionalProperties": False,
    },
    "strict": True,
}


_file_manager_locks: dict[str, asyncio.Lock] = {}
tokenizer = TokenizerOpenAI(model="gpt-4o")


def _get_file_manager_lock_for_context(context: ConversationContext) -> asyncio.Lock:
    """Get or create a conversation-specific lock for file manager operations."""
    if context.id not in _file_manager_locks:
        _file_manager_locks[context.id] = asyncio.Lock()
    return _file_manager_locks[context.id]


def _file_manager_drive_for_context(context: ConversationContext) -> Drive:
    drive_root = storage_directory_for_context(context) / "file_manager"
    return Drive(DriveConfig(root=drive_root))


async def get_file_rankings(context: ConversationContext) -> FileManagerData:
    drive = _file_manager_drive_for_context(context)

    if not drive.file_exists("file_rankings.json"):
        return FileManagerData()

    try:
        with drive.open_file("file_rankings.json") as f:
            data = json.load(f)
            file_manager_data = FileManagerData.model_validate(data)
            return file_manager_data
    except Exception:
        return FileManagerData()


async def save_file_rankings(context: ConversationContext, file_manager_data: FileManagerData) -> None:
    drive = _file_manager_drive_for_context(context)
    data_json = json.dumps(file_manager_data.model_dump(), indent=2).encode("utf-8")
    drive.write(
        content=io.BytesIO(data_json),
        filename="file_rankings.json",
        if_exists=IfDriveFileExistsBehavior.OVERWRITE,
        content_type="application/json",
    )


async def _slow_score_files(
    context: ConversationContext,
    config: AssistantConfigModel,
    attachments_extension: AttachmentsExtension,
    context_management_inspector: ContextManagementInspector,
):
    """
    Score files based on an LLM prompt that looks at the conversation history and the file
    """
    logger.debug(f"Acquiring file manager lock for conversation {context.id}")
    async with asyncio.timeout(500):
        async with _get_file_manager_lock_for_context(context):
            logger.debug(f"File manager lock acquired for conversation {context.id}")
            # Get existing file rankings to avoid recomputing
            existing_file_manager_data = await get_file_rankings(context)

            # Get all the files: attachments, files, and conversation chunks
            attachment_filenames = await attachments_extension.get_attachment_filenames(context)
            doc_editor_filenames = await attachments_extension._inspectors.list_document_filenames(context)
            compaction_data = await get_compaction_data(context)

            # For each file, construct the prompt
            all_files = set(attachment_filenames + doc_editor_filenames)
            for chunk in compaction_data.compaction_data.values():
                all_files.add(chunk.chunk_name)

            # If there are less than max_relevant files, we can skip scoring
            max_relevant_files = config.orchestration.prompts.max_relevant_files
            if len(all_files) <= max_relevant_files:
                return

            percent_files_score_per_turn = config.orchestration.prompts.percent_files_score_per_turn
            minimum_files = 0
            max_files = 100

            # Separate files into those with and without scores
            files_without_scores = [path for path in all_files if path not in existing_file_manager_data.file_data]
            files_with_scores = [path for path in all_files if path in existing_file_manager_data.file_data]

            # Calculate target number of files to score based on percentage
            total_files_to_score = max(
                minimum_files, min(max_files, int(len(all_files) * percent_files_score_per_turn))
            )

            # Start with ALL unscored files up to max_files
            files_to_score = files_without_scores[:max_files]

            # If we haven't reached our target and have remaining budget, sample from scored files
            remaining_slots = total_files_to_score - len(files_to_score)
            if remaining_slots > 0 and files_with_scores:
                additional_files = random.sample(files_with_scores, min(remaining_slots, len(files_with_scores)))
                files_to_score.extend(additional_files)

            files_to_score = files_to_score[:max_files]
            if not files_to_score:
                return

            # Get the conversation history only if we have files to score
            conversation_history = await complete_context_management(
                context, config, attachments_extension, context_management_inspector, []
            )
            conv_history = await convert_oai_messages_to_xml(
                conversation_history,
                filename=None,
            )

            for path in files_to_score:
                # First try to find the path as an editable file
                file_content = await attachments_extension._inspectors.get_file_content(context, path)
                # Then try to find the path as an attachment file
                if file_content is None:
                    file_content = await attachments_extension.get_attachment(context, path)
                # Finally try to find the path as a conversation file.
                if file_content is None:
                    compaction_data = await get_compaction_data(context)
                    for chunk in compaction_data.compaction_data.values():
                        if chunk.chunk_name == path:
                            file_content = chunk.original_conversation_text
                            break
                if file_content is None:
                    continue
                file_content = tokenizer.truncate_str(file_content, max_len=config.orchestration.prompts.token_window)

                system_prompt = render(FILE_SCORE_SYSTEM_PROMPT, current_datetime=pendulum.now().format("YYYY-MM-DD"))
                user_prompt = render(
                    FILE_SCORE_USER_PROMPT,
                    conversation_history=conv_history,
                    file_path=path,
                    file_content=file_content,
                )
                file_score_messages = [
                    ChatCompletionSystemMessageParam(role="system", content=system_prompt),
                    ChatCompletionUserMessageParam(role="user", content=user_prompt),
                ]
                async with create_client(config.generative_ai_fast_client_config.service_config) as client:
                    response = await get_completion(
                        client=client,
                        request_config=config.generative_ai_fast_client_config.request_config,
                        chat_message_params=file_score_messages,
                        tools=None,
                        structured_output=FILE_SCORE_SCHEMA,
                    )
                    try:
                        content = response.choices[0].message.content or "{}"
                        json_message = json.loads(content)
                    except json.JSONDecodeError:
                        json_message = {}

                reasoning = ""
                recency_probability = 0.0
                relevance_probability = 0.0
                if "relevance_probability" in json_message:
                    relevance_data = json_message.get("relevance_probability", {})
                    reasoning = relevance_data.get("brief_reasoning", "")
                    recency_probability = relevance_data.get("recency_probability", 0.0)
                    relevance_probability = relevance_data.get("relevance_probability", 0.0)
                file_relevance = FileRelevance(
                    brief_reasoning=reasoning,
                    recency_probability=recency_probability,
                    relevance_probability=relevance_probability,
                )

                existing_file_manager_data.file_data[path] = file_relevance
                await save_file_rankings(context, existing_file_manager_data)
    logger.debug(f"File manager lock released for conversation {context.id}")


async def _fast_score_files(
    context: ConversationContext,
    config: AssistantConfigModel,
    attachments_extension: AttachmentsExtension,
    context_management_inspector: ContextManagementInspector,
) -> None:
    """
    Score multiple files at once using summaries instead of full content for better performance
    """
    logger.debug(f"Acquiring file manager lock for conversation {context.id}")
    async with asyncio.timeout(500):
        async with _get_file_manager_lock_for_context(context):
            logger.debug(f"File manager lock acquired for conversation {context.id}")
            # Get existing file rankings to avoid recomputing
            existing_file_manager_data = await get_file_rankings(context)

            # Get all the files: attachments, files, and conversation chunks
            attachment_filenames = await attachments_extension.get_attachment_filenames(context)
            doc_editor_filenames = await attachments_extension._inspectors.list_document_filenames(context)
            compaction_data = await get_compaction_data(context)

            # For each file, construct the prompt
            all_files = set(attachment_filenames + doc_editor_filenames)
            for chunk in compaction_data.compaction_data.values():
                all_files.add(chunk.chunk_name)

            # If there are less than max_relevant files, we can skip scoring
            max_relevant_files = config.orchestration.prompts.max_relevant_files
            if len(all_files) <= max_relevant_files:
                return

            percent_files_score_per_turn = config.orchestration.prompts.percent_files_score_per_turn
            minimum_files = 0
            max_files = 40

            # Separate files into those with and without scores
            files_without_scores = [path for path in all_files if path not in existing_file_manager_data.file_data]
            files_with_scores = [path for path in all_files if path in existing_file_manager_data.file_data]

            # If there are unscored files, score up to max_files of them
            if files_without_scores:
                files_to_score = files_without_scores[:max_files]
            else:
                # If all files are scored, use percentage-based scoring for re-scoring
                total_files_to_score = max(
                    minimum_files, min(max_files, int(len(all_files) * percent_files_score_per_turn))
                )
                files_to_score = random.sample(files_with_scores, min(total_files_to_score, len(files_with_scores)))
                files_to_score = files_to_score[:max_files]
            if not files_to_score:
                return

            # Get filesystem metadata for summaries
            filesystem_metadata = await get_filesystem_metadata(context)

            # Build files content string with summaries
            files_content_parts = []
            for path in files_to_score:
                summary = "No summary available yet."
                # Get file summary from filesystem metadata
                file_metadata = filesystem_metadata.get(path)
                if file_metadata and file_metadata.summary:
                    summary = file_metadata.summary
                else:
                    # Fallback: use compacted summary for conversation chunks
                    for chunk in compaction_data.compaction_data.values():
                        if chunk.chunk_name == path:
                            summary = chunk.compacted_text
                            break

                files_content_parts.append(f'<file path="{path}">\n{summary}\n</file>')

            files_content = "\n\n".join(files_content_parts)

            # Get the conversation history only if we have files to score
            conversation_history = await complete_context_management(
                context, config, attachments_extension, context_management_inspector, []
            )
            conv_history = await convert_oai_messages_to_xml(
                conversation_history,
                filename=None,
            )

            # Limit the size of the files_content to ensure we stay within token limits
            files_content = tokenizer.truncate_str(
                files_content,
                max_len=config.generative_ai_fast_client_config.request_config.max_tokens
                - config.orchestration.prompts.max_total_tokens
                - 2000,
            )

            # Create the prompts
            system_prompt = render(MULTI_FILE_SCORE_SYSTEM_PROMPT, current_datetime=pendulum.now().format("YYYY-MM-DD"))
            user_prompt = render(
                MULTI_FILE_SCORE_USER_PROMPT,
                conversation_history=conv_history,
                files_content=files_content,
            )

            multi_file_score_messages = [
                ChatCompletionSystemMessageParam(role="system", content=system_prompt),
                ChatCompletionUserMessageParam(role="user", content=user_prompt),
            ]

            # Score all files at once
            async with create_client(config.generative_ai_fast_client_config.service_config) as client:
                response = await get_completion(
                    client=client,
                    request_config=config.generative_ai_fast_client_config.request_config,
                    chat_message_params=multi_file_score_messages,
                    tools=None,
                    structured_output=MULTI_FILE_SCORE_SCHEMA,
                )
                try:
                    content = response.choices[0].message.content or "{}"
                    json_message = json.loads(content)
                except json.JSONDecodeError:
                    json_message = {}

                file_scores = json_message.get("file_scores", [])
                for file_score in file_scores:
                    file_name = file_score.get("file_name", "")
                    if file_name in files_to_score:
                        reasoning = file_score.get("brief_reasoning", "")
                        recency_probability = file_score.get("recency_probability", 0.0)
                        relevance_probability = file_score.get("relevance_probability", 0.0)

                        file_relevance = FileRelevance(
                            brief_reasoning=reasoning,
                            recency_probability=recency_probability,
                            relevance_probability=relevance_probability,
                        )

                        existing_file_manager_data.file_data[file_name] = file_relevance

                await save_file_rankings(context, existing_file_manager_data)

            # TODO: REMOVE ME
            time.sleep(5)
    logger.debug(f"File manager lock released for conversation {context.id}")


async def task_score_files(
    context: ConversationContext,
    config: AssistantConfigModel,
    attachments_extension: AttachmentsExtension,
    context_management_inspector: ContextManagementInspector,
) -> None:
    if USE_FAST_SCORING:
        await _fast_score_files(context, config, attachments_extension, context_management_inspector)
    else:
        await _slow_score_files(context, config, attachments_extension, context_management_inspector)
