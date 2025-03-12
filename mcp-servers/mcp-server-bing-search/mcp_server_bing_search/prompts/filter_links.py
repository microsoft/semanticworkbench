# Copyright (c) Microsoft. All rights reserved.

from mcp_extensions.llm.llm_types import SystemMessage, UserMessage

FILTER_LINKS_SYSTEM_PROMPT = SystemMessage(
    content="""You are analyzing the links in the Markdown content of a website and identifying the most important URLs for traversing the web.
You will be provided the entire Markdown content of a website, including the links embedded within the content. \
At the end you will also be separately provided the possible links to choose from alongside their ids. \
You should return up to {{max_links}}, **in order of importance**, according to these criteria:
- Form a diverse set of URLs. Do not just return links in order that they appear.
- Are not (near) duplicates
- Are not things like images, videos, or other media
- If the links are traversing a directory-like structure, be sure to choose enough to facilitate traversal, especially ones that would lead to further documentation.
- If you're unsure whether to include a URL, add it anyway since it might lead to novel and interesting content.
- Under no circumstances should you include URLs that may contain harmful, malicious, or otherwise unsafe content."""
)

FILTER_LINKS_USER_PROMPT = UserMessage(
    content="""<website_content>
{{content}}
</website_content>
<links>
{{links}}
</links>"""
)

FILTER_LINKS_MESSAGES = [
    FILTER_LINKS_SYSTEM_PROMPT,
    FILTER_LINKS_USER_PROMPT,
]

LINKS_SCHEMA = {
    "name": "links_filter",
    "schema": {
        "type": "object",
        "properties": {
            "chosen_links": {
                "type": "array",
                "items": {
                    "type": "integer",
                    "description": "id of a chosen link",
                },
                "description": "In order of importance, the ids of chosen links.",
            }
        },
        "required": ["chosen_links"],
        "additionalProperties": False,
    },
    "strict": True,
}
