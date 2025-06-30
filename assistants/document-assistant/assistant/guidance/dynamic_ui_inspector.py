# Copyright (c) Microsoft. All rights reserved.

"""
The inspector state panel for the dynamic UI elements being generated and meant for a user to interact with.
Uses react-jsonschema-form to render the declared UI elements in the workbench app
"""

import io
import json
import logging
from typing import Any

from assistant_drive import Drive, DriveConfig, IfDriveFileExistsBehavior
from semantic_workbench_api_model import workbench_model
from semantic_workbench_api_model.workbench_model import (
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantAppProtocol,
    AssistantConversationInspectorStateDataModel,
    ConversationContext,
    storage_directory_for_context,
)

logger = logging.getLogger(__name__)


async def update_dynamic_ui_state(
    context: ConversationContext,
    new_ui: dict[str, Any] | None,
) -> None:
    """
    Takes in the newly generated UI (by an LLM) and saves it to the assistant drive.
    Each batch of UI elements is saved as a separate section.
    """
    root = storage_directory_for_context(context) / "dynamic_ui"
    drive = Drive(DriveConfig(root=root))

    if new_ui is None:
        return

    # If there's an existing state, retrieve it to update
    existing_ui = {"ui_sections": []}
    if drive.file_exists("ui_state.json"):
        try:
            with drive.open_file("ui_state.json") as f:
                existing_ui = json.loads(f.read().decode("utf-8"))
                if "ui_elements" in existing_ui and "ui_sections" not in existing_ui:
                    # Handle migration from old format
                    existing_ui["ui_sections"] = []
                    if existing_ui["ui_elements"]:
                        existing_ui["ui_sections"].append({
                            "section_id": "section_1",
                            "section_title": "Previous Preferences",
                            "ui_elements": existing_ui["ui_elements"],
                        })
                    del existing_ui["ui_elements"]
        except json.JSONDecodeError:
            logger.warning(f"Error parsing existing UI state for conversation {context.id}")

    # Create a new section for the new UI elements
    if "ui_elements" in new_ui and new_ui["ui_elements"]:
        import time

        section_id = f"section_{int(time.time())}"
        section_title = new_ui.get("section_title", f"Preferences Section {len(existing_ui['ui_sections']) + 1}")

        new_section = {"section_id": section_id, "section_title": section_title, "ui_elements": new_ui["ui_elements"]}

        existing_ui["ui_sections"].append(new_section)

    # Convert the updated dictionary to JSON string and then to bytes
    ui_json = json.dumps(existing_ui, indent=2).encode("utf-8")
    drive.write(
        content=io.BytesIO(ui_json),
        filename="ui_state.json",
        if_exists=IfDriveFileExistsBehavior.OVERWRITE,
        content_type="application/json",
    )

    # Update the dynamic UI panel if it's already open
    await context.send_conversation_state_event(
        workbench_model.AssistantStateEvent(
            state_id="dynamic_ui",
            event="updated",
            state=None,
        )
    )


async def get_dynamic_ui_state(context: ConversationContext) -> dict[str, Any]:
    """
    Gets the current state of the dynamic UI elements from the assistant drive for use
    by the assistant in LLM calls or for the app to display in the inspector panel.
    """
    root = storage_directory_for_context(context) / "dynamic_ui"
    drive = Drive(DriveConfig(root=root))
    if not drive.file_exists("ui_state.json"):
        return {}

    try:
        with drive.open_file("ui_state.json") as f:
            ui_json = f.read().decode("utf-8")
            return json.loads(ui_json)
    except (json.JSONDecodeError, FileNotFoundError):
        logger.exception("Error reading dynamic UI state")
        return {}


def convert_generated_config(
    component_type: str,
    generated_config: dict[str, Any] | str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Converts the generated UI component by an LLM into a JSON schema and UI schema
    for rendering by the app's JSON schema renderer.
    """
    # Checkbox and dropdown will have a title and options,
    # whereas a textbox will only have the title of the textbox
    if isinstance(generated_config, dict):
        title = generated_config.get("title", "")
        options = generated_config.get("options", [])
    else:
        title = generated_config
        options = []
    enum_items = [x.get("value", "") for x in options if isinstance(x, dict)]

    match component_type:
        case "checkboxes":
            schema = {
                title: {
                    "type": "array",
                    "title": title,
                    "items": {
                        "type": "string",
                        "enum": enum_items,
                    },
                    "uniqueItems": True,
                }
            }
            ui_schema = {
                title: {
                    "ui:widget": "checkboxes",
                    "ui:options": {"inline": True},
                }
            }
            return schema, ui_schema
        case "dropdown":
            schema = {
                title: {
                    "type": "string",
                    "title": title,
                    "enum": enum_items,
                }
            }
            ui_schema = {
                title: {
                    "ui:widget": "select",
                    "ui:style": {"width": "250px"},
                }
            }
            return schema, ui_schema
        case "textbox":
            schema = {
                title: {
                    "type": "string",
                    "title": title,
                }
            }
            ui_schema = {
                title: {
                    "ui:widget": "textarea",
                    "ui:placeholder": "",
                    "ui:style": {
                        "width": "500px",
                        "resize": "vertical",
                    },
                    "ui:options": {"rows": 2},
                }
            }
            return schema, ui_schema
        case _:
            logger.warning(f"Unknown component type: {component_type}")
            return {}, {}


class DynamicUIInspector:
    def __init__(
        self,
        app: AssistantAppProtocol,
        state_id: str = "dynamic_ui",
        display_name: str = "Dynamic User Preferences",
        description: str = "Choose your preferences",
    ) -> None:
        self._state_id = state_id
        self._display_name = display_name
        self._description = description

        app.add_inspector_state_provider(state_id=self.state_id, provider=self)

    @property
    def state_id(self) -> str:
        return self._state_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def description(self) -> str:
        return self._description

    async def is_enabled(self, context: ConversationContext) -> bool:
        # TODO: Base this on the config
        return True

    async def get(self, context: ConversationContext) -> AssistantConversationInspectorStateDataModel:
        """
        Retrieves the state of the dynamic UI elements and returns it in a
        format suitable for the inspector state panel in the workbench app's JSON schema renderer.
        Each section of UI elements is rendered as a separate collapsible section.
        Only the last two sections are expanded by default.
        """
        saved_ui_state = await get_dynamic_ui_state(context)

        schema = {
            "type": "object",
            "properties": {
                "assistant_generated_preferences": {
                    "type": "object",
                    "title": "Document Assistant Generated Preferences",
                    "properties": {},  # To be populated dynamically with sections
                }
            },
        }

        ui_schema = {
            "ui:options": {
                "hideTitle": True,
                "collapsible": False,
            },
            "assistant_generated_preferences": {
                "ui:options": {
                    "collapsible": True,
                    "collapsed": False,
                },
                # To be populated dynamically with sections
            },
            "ui:submitButtonOptions": {
                "submitText": "Save Preferences",
            },
        }

        # Setup sections in schema and ui_schema
        sections = saved_ui_state.get("ui_sections", [])
        saved_form_data = saved_ui_state.get("form_data", {})
        form_data = {"assistant_generated_preferences": {}}

        # If no sections but old format elements exist, convert them
        if not sections and "ui_elements" in saved_ui_state and saved_ui_state["ui_elements"]:
            sections = [
                {
                    "section_id": "legacy_section",
                    "section_title": "Preferences",
                    "ui_elements": saved_ui_state["ui_elements"],
                }
            ]

        # Calculate which sections should be expanded
        section_count = len(sections)
        keep_expanded_indices = (
            {section_count - 1, section_count - 2} if section_count >= 2 else set(range(section_count))
        )

        # Process each section
        for idx, section in enumerate(sections):
            section_id = section["section_id"]
            section_title = section["section_title"]

            # Determine if this section should be collapsed
            is_collapsed = idx not in keep_expanded_indices

            # Add section to schema
            schema["properties"]["assistant_generated_preferences"]["properties"][section_id] = {
                "type": "object",
                "title": section_title,
                "properties": {},
            }

            # Add section to UI schema
            ui_schema["assistant_generated_preferences"][section_id] = {
                "ui:options": {
                    "collapsible": True,
                    "collapsed": is_collapsed,
                }
            }

            # Process elements in this section
            for generated_component in section.get("ui_elements", []):
                component_type, component_config = next(iter(generated_component.items()))
                generated_schema, generated_ui_schema = convert_generated_config(component_type, component_config)

                # Get the title from the generated schema
                for prop_title, prop_schema in generated_schema.items():
                    # Add to section schema
                    schema["properties"]["assistant_generated_preferences"]["properties"][section_id][
                        "properties"
                    ].update({prop_title: prop_schema})

                    # Add to section UI schema
                    ui_schema["assistant_generated_preferences"][section_id].update({
                        prop_title: generated_ui_schema[prop_title]
                    })

                    # Add any existing form data
                    if saved_form_data and "assistant_generated_preferences" in saved_form_data:
                        if prop_title in saved_form_data["assistant_generated_preferences"]:
                            if section_id not in form_data["assistant_generated_preferences"]:
                                form_data["assistant_generated_preferences"][section_id] = {}
                            form_data["assistant_generated_preferences"][section_id][prop_title] = saved_form_data[
                                "assistant_generated_preferences"
                            ][prop_title]

        return AssistantConversationInspectorStateDataModel(
            data=form_data,
            json_schema=schema,
            ui_schema=ui_schema,
        )

    async def set(
        self,
        context: ConversationContext,
        data: dict[str, Any],
    ) -> None:
        """
        Saves the form data submitted when the user saves their preferences in the inspector panel.
        After saving, it also sends a message to the conversation with the changes made as a special log message.
        Handles the sectioned UI structure.
        """
        root = storage_directory_for_context(context) / "dynamic_ui"
        drive = Drive(DriveConfig(root=root))

        # First gets the existing state
        existing_ui = {"ui_sections": []}
        previous_form_data = {}
        if drive.file_exists("ui_state.json"):
            try:
                with drive.open_file("ui_state.json") as f:
                    existing_ui = json.loads(f.read().decode("utf-8"))
                    previous_form_data = existing_ui.get("form_data", {}).get("assistant_generated_preferences", {})
            except json.JSONDecodeError:
                logger.warning(f"Error parsing existing UI state for conversation {context.id}")

        # Then add the new form data to the existing state.
        new_form_data = {}
        if "assistant_generated_preferences" in data:
            # Flatten the sectioned form data for storage
            flattened_data = {}
            for section_id, section_data in data["assistant_generated_preferences"].items():
                flattened_data.update(section_data)

            new_form_data = flattened_data
            existing_ui["form_data"] = {"assistant_generated_preferences": flattened_data}  # type: ignore

        # Save the updated state back to the drive
        ui_json = json.dumps(existing_ui).encode("utf-8")
        drive.write(
            content=io.BytesIO(ui_json),
            filename="ui_state.json",
            if_exists=IfDriveFileExistsBehavior.OVERWRITE,
            content_type="application/json",
        )

        # Construct a message for the assistant about the changes
        message_content = "User updated UI: "
        changes = []
        for title, value in new_form_data.items():
            if title not in previous_form_data:
                changes.append(f"Set '{title}' to '{value}'")
            elif previous_form_data[title] != value:
                changes.append(f"Changed '{title}' to '{value}'")
        for title in previous_form_data:
            if title not in new_form_data:
                changes.append(f"Removed selection in '{title}'")

        if changes:
            message_content += "\n- " + "\n- ".join(changes)
        else:
            message_content += "No changes detected"

        # Send message about the UI changes
        await context.send_messages(
            NewConversationMessage(
                content=message_content,
                message_type=MessageType.log,
                metadata={},
            )
        )
