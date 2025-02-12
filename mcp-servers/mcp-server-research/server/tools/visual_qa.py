import base64
import mimetypes
import os
from dataclasses import dataclass
from typing import Optional
from typing_extensions import TypedDict

import requests
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

class ImageAnalysisResult(BaseModel):
    """Result of analyzing an image with or without a specific question."""
    description: str = Field(description="Detailed description or answer about the image")
    is_caption: bool = Field(description="Whether this is a general caption (True) or specific answer (False)")

@dataclass
class VisualDependencies:
    """Dependencies required for visual analysis."""
    api_key: str
    headers: dict[str, str]

class ImageQuery(TypedDict, total=False):
    """Structure for image analysis query"""
    image_path: str
    question: Optional[str]

def encode_image(image_path: str) -> str:
    """Encode an image file to base64."""
    if image_path.startswith("http"):
        # Download image from URL
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        response = requests.get(
            image_path,
            headers={"User-Agent": user_agent},
            stream=True
        )
        response.raise_for_status()
        return base64.b64encode(response.content).decode("utf-8")

    # Read local file
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Initialize the visual QA agent
visual_qa_agent = Agent(
    'openai:gpt-4o',
    deps_type=VisualDependencies,
    result_type=ImageAnalysisResult,
    system_prompt=(
        "You are a visual analysis assistant. Analyze images and provide detailed "
        "descriptions or answer specific questions about them. Be detailed and accurate "
        "in your observations."
    )
)

@visual_qa_agent.tool
async def analyze_image(
    ctx: RunContext[VisualDependencies],
    image_path: str,
    question: Optional[str] = None
) -> ImageAnalysisResult:
    """Analyze an image and optionally answer a specific question about it.

    Args:
        ctx: Runtime context containing dependencies
        image_path: Path to the image file (local path or URL)
        question: Optional specific question about the image

    Returns:
        Analysis result containing the description and whether it's a caption
    """
    if not question:
        question = "Please write a detailed caption for this image."
        is_caption = True
    else:
        is_caption = False

    # Get image mime type and encode
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg"  # Default to JPEG if can't determine
    base64_image = encode_image(image_path)

    # Prepare the API request
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    },
                ],
            }
        ],
        "max_tokens": 1000,
    }

    # Make the API call
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=ctx.deps.headers,
        json=payload
    )
    response.raise_for_status()

    try:
        output = response.json()["choices"][0]["message"]["content"]
    except KeyError as e:
        raise ValueError(f"Unexpected API response format: {response.json()}") from e

    return ImageAnalysisResult(
        description=output,
        is_caption=is_caption
    )

def create_visual_qa_agent() -> tuple[Agent[VisualDependencies, ImageAnalysisResult], VisualDependencies]:
    """Create and configure a visual QA agent with proper dependencies."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    deps = VisualDependencies(
        api_key=api_key,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )

    return visual_qa_agent, deps

# Example usage:
async def main():
    agent, deps = create_visual_qa_agent()

    # Example with just caption
    result = await agent.run(
        "Please analyze this image",
        deps=deps,
    )
    print(f"Caption: {result.data.description}")

    # Example with specific question
    result = await agent.run(
        "What colors are present in this image?",
        deps=deps,
    )
    print(f"Answer: {result.data.description}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
