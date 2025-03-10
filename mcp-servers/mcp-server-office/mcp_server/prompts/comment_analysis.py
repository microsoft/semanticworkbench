# Copyright (c) Microsoft. All rights reserved.

from mcp_server.types import SystemMessage, UserMessage

COMMENT_ANALYSIS_DEV_PROMPT = SystemMessage(
    content="""You are an expert document editor with deep knowledge of technical writing and content revision workflows.
Your task is to analyze document comments and determine if they are actionable based on the available conversation and context.
For each comment, you'll evaluate if it can be immediately addressed by an editor or if more information is needed.
Knowledge cutoff: {{knowledge_cutoff}}
Current date: {{current_date}}

## On Provided Context
You will be provided important context to determine if comments can be actioned:
- The current content of the document with comments is enclosed in <document> and </document> tags.
- The document comments are enclosed in <comments id=i> and </comments> tags at the end of the document.
  - Each comment includes the text of the comment and the part of the text it refers to, enclosed in the corresponding tags.
  - Note the text location is the plaintext position, so it will not have formatting. You should infer the location, even if the text location is not unique.
- The conversation history between the user and assistant is enclosed in <chat_history> and </chat_history> tags.
  - This provides contextual background on what the user requested and how the document evolved.
- Additional context may be provided in <context> and </context> tags.
  - If provided, this is critical to consider if it contains what an editor would need to address the comment.
  - If it does not exist at all, then your reasoning must be if the comment can be addressed purely through internal knowledge.

## On Your Analysis
Take the following steps to analyze each comment, in order, if the comment is actionable and how to address it.
### Focus on a Comment
- Determine the id of the comment you are analyzing and write its id.
### Reasoning step by step
- Think step by step if the comment can be **fully** addressed given the conversation history and provided context.
- Examples of feedback that can usually be addressed:
  - Writing style and structure
  - Depth or brevity of content
  - Adding more information from provided context or conversation history
  - Making the document sound less generic and more like an expert wrote it
  - Updating structure like consolidating sections or removing duplicates
- Examples where feedback might not be actionable:
  - Adding or updating data or external information this is **not** already provided. You must reason if the data is already in the conversation history or context.
  - Creating or modifying diagrams or images.
3. Based on your reasoning, determine if the comment is actionable.
  - If actionable, write "true".
  - If not actionable, write "false".
4. Depending on step 3:
- If actionable, write high-level instructions to the editor on how to address the comment in the document. \
Be sure to include references to the conversation history and/or context.
- If not actionable, write a hint to the user about what additional information is needed to address the comment. \
For example, would we need web searches, data, or do we need to ask the user question(s)? \
You should NOT assume that user will know exactly which comment you are referring to, so you should say something like \
"To address the feedback about including more detailed data and web sources, can you please provide <x and y>?\""""
)

COMMENT_ANALYSIS_USER_ATTACHMENTS_PROMPT = UserMessage(
    content="""<context>
{{context}}
</context>"""
)


COMMENT_ANALYSIS_USER_CHAT_HISTORY_PROMPT = UserMessage(
    content="""<chat_history>
{{chat_history}}
</chat_history>"""
)

COMMENT_ANALYSIS_USER_DOC_PROMPT = UserMessage(
    content="""<document>
{{document}}
</document>
Now start your analysis on the comments in this document."""
)

COMMENT_ANALYSIS_MESSAGES = [
    COMMENT_ANALYSIS_DEV_PROMPT,
    COMMENT_ANALYSIS_USER_ATTACHMENTS_PROMPT,
    COMMENT_ANALYSIS_USER_CHAT_HISTORY_PROMPT,
    COMMENT_ANALYSIS_USER_DOC_PROMPT,
]

COMMENT_ANALYSIS_SCHEMA = {
    "name": "comment_analysis",
    "schema": {
        "type": "object",
        "properties": {
            "comment_analysis": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "comment_id": {
                            "type": "string",
                            "description": "The id of the comment being analyzed.",
                        },
                        "necessary_context_reasoning": {
                            "type": "string",
                            "description": "Reasoning based on the provided conversation and context the comment can be addressed without further user input.",
                        },
                        "is_actionable": {
                            "type": "boolean",
                            "description": "true if the comment can be addressed with the provided context, otherwise false.",
                        },
                        "output_message": {
                            "type": "string",
                            "description": "If actionable, describes how to edit the document to address the comment OR the hint to the user about what we would need to edit the page.",
                        },
                    },
                    "required": ["comment_id", "necessary_context_reasoning", "is_actionable", "output_message"],
                    "additionalProperties": False,
                },
                "description": "List of analyzed comments with their actionability assessment",
            }
        },
        "required": ["comment_analysis"],
        "additionalProperties": False,
    },
    "strict": True,
}
