# State Inspectors

## Overview

State inspectors provide a way to visualize and interact with an assistant's internal state. Each assistant can have multiple state inspectors, with the `config` editor being a required inspector for all assistants.

State inspectors can be used for:
- Debugging assistant behavior
- Monitoring internal state changes
- Providing interactive interfaces for modifying assistant state
- Exposing data and attachments for user inspection

## Accessing State Inspectors

State inspectors are available in the assistant's conversation view. To access them:

1. Join a conversation with an assistant
2. Click the `Show Inspectors` button in the conversation interface
3. A tabbed view will appear with each tab representing a different state

## Rendering Methods

The inspector view will render state based on its content:

1. **Content-based Rendering**: If the state's `data` property contains a `content` key with a string value, it will be rendered as:
   - Markdown for formatted text
   - HTML for rich content
   - Plain text for simple content

2. **Schema-based Rendering**: If the state includes a `JsonSchema` property, a custom UI will be generated based on the schema:
   - Form elements will be created for each schema property
   - If a `UISchema` property is provided, it will customize the UI appearance
   - Validation will follow the schema rules

3. **JSON Fallback**: If neither of the above applies, the state will be rendered as formatted JSON.

## Interactive State Editing

When a state includes a `JsonSchema` property, the inspector provides editing capabilities:

1. An edit button will appear in the inspector
2. Clicking it opens a dialog with form elements based on the schema
3. Users can modify values and save changes
4. Changes are sent to the assistant, which is notified of the update

## Attachments Support

State inspectors can include file attachments:

1. If a state contains `attachments` data, files will be displayed with download options
2. Users can download attachments for local inspection
3. Common file types may have preview capabilities

## Implementing State Inspectors

Assistants can implement state inspectors by:

1. Defining data models with appropriate JSON schemas
2. Exposing state through the assistant service API
3. Handling state change notifications from the user interface
4. Updating state in response to internal events

## Example Schema

```json
{
  "JsonSchema": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "title": "Name"
      },
      "enabled": {
        "type": "boolean",
        "title": "Enabled"
      },
      "settings": {
        "type": "object",
        "properties": {
          "threshold": {
            "type": "number",
            "title": "Threshold",
            "minimum": 0,
            "maximum": 1
          }
        }
      }
    }
  },
  "UISchema": {
    "settings": {
      "ui:expandable": true
    }
  },
  "data": {
    "name": "My Assistant",
    "enabled": true,
    "settings": {
      "threshold": 0.7
    }
  }
}
```

State inspectors provide powerful debugging and interaction capabilities for both developers and users of the Semantic Workbench platform.
