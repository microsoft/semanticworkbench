# Copyright (c) Microsoft. All rights reserved.

from mcp_extensions.llm.llm_types import SystemMessage, UserMessage

CLEAN_WEBSITE_SYSTEM_PROMPT = SystemMessage(
    content="""You are responsible for parsing website content to leave the most important parts exactly as they were in the original website.
You will be given website content that has been processed using markdownify. \
It is your job to do a cleaning pass on the content to remove any unneeded content. \
You should remove aspects that are artifacts of the HTML to markdown conversion and do not help with the understanding of the content \
such as navigation, extraneous links, dropdowns, images, etc.
- You should preserve things like formatting of content itself.
- If the content is long, you should only include the most important 4000 tokens of text.
- If the content is documentation, an article, blog, etc you absolutely must return the content in its entirety.
- Be sure to include authors and dates. Also preserve important data, if it exists, like GitHub stars, viewership, things that hint at recency, etc.
- It is critical that the content you wish to keep, you copy WORD FOR WORD.
- Do not wrap the content in a markdown code block.
- NEVER summarize, you are only allowed to output the content verbatim."""
)

CLEAN_WEBSITE_USER_PROMPT = UserMessage(
    content="""<website_content>
{{content}}
</website_content>"""
)

CLEAN_WEBSITE_MESSAGES = [
    CLEAN_WEBSITE_SYSTEM_PROMPT,
    CLEAN_WEBSITE_USER_PROMPT,
]
