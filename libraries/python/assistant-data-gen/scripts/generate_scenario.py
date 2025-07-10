# Copyright (c) Microsoft. All rights reserved.

"""
Generate new evaluation scenarios using Pydantic AI.

This script:
1. Reads existing scenarios from the YAML config
2. Uses Pydantic AI to generate a new, non-redundant scenario
3. Allows user review and approval
4. Appends the approved scenario to the YAML config file
"""

import argparse
import asyncio
from pathlib import Path

from assistant_data_gen.config import EvaluationConfig
from assistant_data_gen.pydantic_ai_utils import create_model
from dotenv import load_dotenv
from liquid import render
from pydantic import BaseModel, Field
from pydantic_ai import Agent

load_dotenv()

SYSTEM_PROMPT = """You are a creative scenario generator for testing AI assistants.

Your task is to create realistic, varied scenarios that test different aspects of the assistant's capabilities. Each scenario should:
- Be distinct from all existing scenarios
- Test different assistant capabilities
- Include realistic user goals and motivations
- Provide a clear, step-by-step conversation flow
- Estimate appropriate resource_total (conversation turns needed, go higher than you might think)"""

USER_PROMPT = """This is what the assistant is about and can do:
{{assistant_details}}

Here are the existing scenarios:
{{existing_scenarios}}

Now create a new scenario!"""


class GeneratedScenario(BaseModel):
    """A generated scenario with description and conversation flow."""

    description: str = Field(description="The scenario description for role-playing")
    gce_conversation_flow: str = Field(description="Step-by-step conversation flow instructions")
    resource_total: int = Field(description="Estimated number of conversation turns needed", ge=10, le=100)


def load_existing_scenarios(config_path: Path) -> EvaluationConfig:
    """Load existing scenarios from the config file."""
    return EvaluationConfig.load_from_yaml(config_path)


def format_existing_scenarios(config: EvaluationConfig) -> str:
    """Format existing scenarios for the AI prompt."""
    scenarios_text = ""
    for i, scenario in enumerate(config.scenarios):
        scenarios_text += f"Scenario {i + 1}:\n"
        scenarios_text += f"Description: {scenario.description}\n"
        scenarios_text += f"Flow: {scenario.gce_conversation_flow}"
    return scenarios_text


async def generate_new_scenario(config: EvaluationConfig) -> GeneratedScenario:
    model = create_model(config.general.gce_provider)
    agent = Agent(
        model=model,
        output_type=GeneratedScenario,
        system_prompt=SYSTEM_PROMPT,
    )
    existing_scenarios = format_existing_scenarios(config)
    prompt = render(
        USER_PROMPT,
        **{
            "assistant_details": config.general.assistant_details,
            "existing_scenarios": existing_scenarios,
        },
    )
    result = await agent.run(prompt)
    return result.output


def display_scenario(scenario: GeneratedScenario) -> None:
    """Display the generated scenario for user review."""
    print("\n" + "=" * 80)
    print("GENERATED SCENARIO")
    print("=" * 80)
    print("\nDescription:")
    print(f"{scenario.description}")
    print("\nConversation Flow:")
    print(f"{scenario.gce_conversation_flow}")
    print(f"\nEstimated Resource Total: {scenario.resource_total}")
    print("=" * 80)


def get_user_approval() -> bool | None | str:
    """Get user approval for the generated scenario."""
    while True:
        response = (
            input("\nDo you want to add this scenario to the config? (y/n/r for regenerate, q to quit): ")
            .lower()
            .strip()
        )
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        elif response in ["r", "regenerate"]:
            return None
        elif response in ["q", "quit"]:
            return "quit"
        else:
            print("Please enter 'y' (yes), 'n' (no), 'r' (regenerate), or 'q' (quit)")


def append_scenario_to_config(config_path: Path, scenario: GeneratedScenario) -> None:
    """Append the new scenario to the YAML config file."""

    def format_multiline_text(text: str) -> list[str]:
        """Format text for YAML >- style, converting single newlines to double newlines."""
        lines = []
        # For YAML >- folding, we need double newlines to preserve single newlines in output
        # So convert single newlines to double newlines first
        text = text.replace("\n", "\n\n")
        text_lines = text.strip().split("\n")
        for line in text_lines:
            line = line.strip()
            if not line:
                lines.append("      ")
                continue

            # Word wrap long lines to keep under 80 characters
            words = line.split()
            current_line = ""
            for word in words:
                if len(current_line + " " + word) > 80 and current_line:
                    lines.append(f"      {current_line.strip()}")
                    current_line = word
                else:
                    current_line += " " + word if current_line else word
            if current_line:
                lines.append(f"      {current_line.strip()}")
        return lines

    scenario_yaml = []
    scenario_yaml.append("  - description: >-")
    scenario_yaml.extend(format_multiline_text(scenario.description))
    scenario_yaml.append("    gce_conversation_flow: >-")
    scenario_yaml.extend(format_multiline_text(scenario.gce_conversation_flow))
    scenario_yaml.append(f"    resource_total: {scenario.resource_total}")
    with config_path.open("a", encoding="utf-8") as f:
        f.write("\n")
        f.write("\n".join(scenario_yaml))
        f.write("\n")

    print(f"\n✅ Scenario successfully added to {config_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default=str(Path(__file__).parents[1] / "configs" / "document_assistant_example_config.yaml"),
        help="Path to the configuration YAML file",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    config_path = Path(args.config)

    while True:
        config = load_existing_scenarios(config_path)
        scenario = await generate_new_scenario(config)
        display_scenario(scenario)
        approval = get_user_approval()

        if approval is True:
            append_scenario_to_config(config_path, scenario)
            print("🎉 New scenario added successfully! Continuing to generate next scenario...")
        elif approval is False:
            print("❌ Scenario rejected. Continuing to generate next scenario...")
        elif approval == "quit":
            print("👋 Goodbye!")
            return
        else:
            print("🔄 Regenerating scenario...")
            continue


if __name__ == "__main__":
    asyncio.run(main())
