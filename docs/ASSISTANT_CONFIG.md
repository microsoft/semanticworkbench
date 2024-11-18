# Semantic Workbench Assistant Configuration

This document outlines the serialized configuration format for Semantic Workbench Assistants. These configurations can be exported from the assistant configuration page, allowing you to edit by hand and then import any changes.

This process is especially useful for guided conversation-based assistants. These configurations typically require detailed customization, including the description of artifacts, conversation flows, rules, and context settings.

### Recommended Format

For editing guided conversation assistants, we recommend using the YAML format. This format offers better readability and ease of handling complex configurations.

### Configuration Scope

The complete configuration export includes sections specific to the assistant in use, as well as common sections for request, service, and content safety configurations. You may choose to omit these common sections if you prefer to use default or current values upon import.

### Partial Imports

The import process supports partial updates. As long as the path is correctly represented, you can import even a single deeply nested value. This feature is particularly beneficial for sending complicated patches to existing configurations within different environments.

---

## Example: Guided Conversation Agent Configuration for Acrostic Poem

Below is an explanation using the YAML example for a guided conversation agent designed to help a student create an acrostic poem.

### `guided_conversation_agent`

- **Artifact**:

  - A JSON schema as a string that defines fields such as:
    - `student_poem`: Captures the acrostic poem written by the student.
    - `initial_feedback`: Initial feedback on the poem.
    - `final_feedback`: Feedback after revisions.
    - `inappropriate_behavior`: Logs any inappropriate attempts during the session.

- **Rules**:

  - Examples include:
    - "DO NOT write the poem for the student."
    - "Terminate the conversation immediately if inappropriate content is requested."

- **Conversation Flow**:

  - Outlines the interaction:
    - Start by explaining what an acrostic poem is.
    - Guide the student in writing their own poem.
    - Review and give feedback on the poem.
  - **Advice**: Number each step for clarity.

- **Context**:

  - Describes the educational interaction:
    - The assistant works one-on-one with a 4th-grade student in a supervised computer lab.

- **Resource Constraint**:
  - Defines limits like:
    - The number of turns (e.g., 10 turns maximum).

### Example YAML Snippet

```yaml
guided_conversation_agent:
  definition:
    artifact: |-
      {
        "properties": {
            "student_poem": {
              "description": "The acrostic poem written by the student.",
              "title": "Student Poem",
              "type": "string"
            },
            "initial_feedback": {
              "description": "Feedback on the student's final revised poem.",
              "title": "Initial Feedback",
              "type": "string"
            },
            "final_feedback": {
              "description": "Feedback on how the student was able to improve their poem.",
              "title": "Final Feedback",
              "type": "string"
            },
            "inappropriate_behavior": {
              "description": "\nList any inappropriate behavior the student attempted while chatting with you.\nIt is ok to leave this field Unanswered if there was none.\n",
              "items": {
                "type": "string"
              },
              "title": "Inappropriate Behavior",
              "type": "array"
            }
          },
          "required": [
            "student_poem",
            "initial_feedback",
            "final_feedback",
            "inappropriate_behavior"
          ],
          "title": "ArtifactModel",
          "type": "object"
      }
    rules:
      - "DO NOT write the poem for the student."
      - "Terminate the conversation immediately if inappropriate content is requested."
    conversation_flow: |-
      1. Start by explaining what an acrostic poem is.
      2. Then give the following instructions for how to go ahead and write one:
         1. Choose a word or phrase that will be the subject of your acrostic poem.
         2. Write the letters of your chosen word or phrase vertically down the page.
         3. Think of a word or phrase that starts with each letter of your chosen word or phrase.
         4. Write these words or phrases next to the corresponding letters to create your acrostic poem.
      3. Then give the following example of a poem where the word or phrase is HAPPY:
         Having fun with friends all day,
         Awesome games that we all play.
         Pizza parties on the weekend,
         Puppies we bend down to tend,
         Yelling yay when we win the game
      4. Finally have the student write their own acrostic poem using the word or phrase of their choice. Encourage them to be creative and have fun with it. After they write it, you should review it and give them feedback on what they did well and what they could improve on. Have them revise their poem based on your feedback and then review it again.
    context: |-
      You are working one-on-one with a 4th-grade student who is chatting with you in the computer lab at school while being supervised by their teacher.
    resource_constraint:
      quantity: 10
      unit: turns
      mode: exact
```

---

## Complete Field Descriptions

### `guided_conversation_agent`

- **Artifact**:

  - Represents a structured schema for data the assistant interacts with.
  - **Key Features**:
    - Supports various data types, including strings, numbers, arrays, and objects.
  - **Code Example**:
    ```yaml
    artifact: |-
      {
        "title": "ArtifactModel",
        "type": "object",
        "properties": {
          "string_field": {
            "type": "string",
            "description": "A basic string field for text input."
          },
          "numeric_field": {
            "type": "number",
            "description": "A numeric field for quantifiable data."
          },
          "list_field": {
            "type": "array",
            "items": {
              "type": "string"
            },
            "description": "A list field to hold multiple string entries."
          },
          "object_field": {
            "type": "object",
            "properties": {
              "subfield1": {
                "type": "string",
                "description": "Description for subfield 1."
              },
              "subfield2": {
                "type": "number",
                "description": "Description for subfield 2."
              }
            },
            "description": "An object field containing subfields."
          }
        },
        "required": [
          "string_field",
          "numeric_field",
          "list_field",
          "object_field"
        ]
      }
    ```

- **Rules**:

  - Guidelines outlining the assistant's permissible actions.
  - Ensure adherence to task objectives and ethical standards.

- **Conversation Flow**:

  - Defines the order and logic of interactions between the assistant and user.
  - **Advice**: Number each step to ensure clarity and logical progression.

- **Context**:

  - Provides background and setting for the assistant's role.
  - Helps tailor interactions to the user's environment.

- **Resource Constraint**:
  - Specifies constraints like duration or number of interactions.
  - Useful for managing conversation flow and time efficiency.

### `request_config`

- **Max Tokens**: Controls total token usage in requests.
- **Response Tokens**: Allocates tokens for model responses.
- **OpenAI Model**: Specifies the model type used, such as GPT-4.

### `service_config`

- **Service Type**: Describes the type of AI service (e.g., Azure OpenAI).
- **Auth Config**: Includes method and credentials for authentication.

### `content_safety_config`

- **Service Config**: Details for content safety measures.
  - **Warn/Fail at Severity**: Levels indicating content risk.
  - **Azure Content Safety Endpoint**: Endpoint for evaluating content safety.

## JSON Schema (Complete Configuration)

```json
{
  "type": "object",
  "properties": {
    "guided_conversation_agent": {
      "type": "object",
      "properties": {
        "definition": {
          "type": "object",
          "properties": {
            "artifact": {
              "type": "string",
              "description": "String representation of the JSON schema for the artifact."
            },
            "rules": {
              "type": "array",
              "items": {
                "type": "string"
              },
              "description": "Guidelines for the assistant's behavior."
            },
            "conversation_flow": {
              "type": "string",
              "description": "Step-by-step guide to interacting with the user."
            },
            "context": {
              "type": "string",
              "description": "Describes the interaction setting."
            },
            "resource_constraint": {
              "type": "object",
              "properties": {
                "quantity": {
                  "type": "integer"
                },
                "unit": {
                  "type": "string"
                },
                "mode": {
                  "type": "string"
                }
              },
              "description": "Limits on conversation resources."
            }
          },
          "required": [
            "artifact",
            "rules",
            "conversation_flow",
            "context",
            "resource_constraint"
          ]
        }
      }
    },
    "request_config": {
      "type": "object",
      "properties": {
        "max_tokens": {
          "type": "integer"
        },
        "response_tokens": {
          "type": "integer"
        },
        "openai_model": {
          "type": "string"
        }
      },
      "description": "Configures parameters for AI model interactions."
    },
    "service_config": {
      "type": "object",
      "properties": {
        "service_type": {
          "type": "string"
        },
        "auth_config": {
          "type": "object",
          "properties": {
            "auth_method": {
              "type": "string"
            }
          }
        }
      },
      "description": "Manages connection details and authentication."
    },
    "content_safety_config": {
      "type": "object",
      "properties": {
        "service_config": {
          "type": "object",
          "properties": {
            "service_type": {
              "type": "string"
            },
            "warn_at_severity": {
              "type": "integer"
            },
            "fail_at_severity": {
              "type": "integer"
            },
            "auth_config": {
              "type": "object",
              "properties": {
                "auth_method": {
                  "type": "string"
                }
              }
            }
          }
        }
      },
      "description": "Ensures all generated content adheres to safety standards."
    }
  },
  "required": [
    "guided_conversation_agent",
    "request_config",
    "service_config",
    "content_safety_config"
  ]
}
```

## YAML Schema (Complete Configuration)

```yaml
type: object
properties:
  guided_conversation_agent:
    type: object
    properties:
      definition:
        type: object
        properties:
          artifact:
            type: string
            description: "String representation of the JSON schema for the artifact."
          rules:
            type: array
            items:
              type: string
            description: "Guidelines for the assistant's behavior."
          conversation_flow:
            type: string
            description: "Step-by-step guide to interacting with the user."
          context:
            type: string
            description: "Describes the interaction setting."
          resource_constraint:
            type: object
            properties:
              quantity:
                type: integer
              unit:
                type: string
              mode:
                type: string
            description: "Limits on conversation resources."
        required:
          - artifact
          - rules
          - conversation_flow
          - context
          - resource_constraint
  request_config:
    type: object
    properties:
      max_tokens:
        type: integer
      response_tokens:
        type: integer
      openai_model:
        type: string
    description: "Configures parameters for AI model interactions."
  service_config:
    type: object
    properties:
      service_type:
        type: string
      auth_config:
        type: object
        properties:
          auth_method:
            type: string
    description: "Manages connection details and authentication."
  content_safety_config:
    type: object
    properties:
      service_config:
        type: object
        properties:
          service_type:
            type: string
          warn_at_severity:
            type: integer
          fail_at_severity:
            type: integer
          auth_config:
            type: object
            properties:
              auth_method:
                type: string
        description: "Ensures all generated content adheres to safety standards."
    description: "Content safety settings."
required:
  - guided_conversation_agent
  - request_config
  - service_config
  - content_safety_config
```

## Generic Artifact Schema

### JSON Schema

Note: When serializing the artifact model within a configuration, ensure the JSON schema is represented as a string. Set the title to "ArtifactModel" and the type to "object" for clarity and consistency.

```json
{
  "type": "object",
  "properties": {
    "field_name": {
      "type": "string",
      "description": "Description of the field."
    },
    "another_field": {
      "type": "number",
      "description": "Description for a numeric field."
    },
    "list_field": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Description for a list field."
    }
  },
  "required": ["field_name", "another_field", "list_field"]
}
```

### YAML Schema

Note: When serializing the artifact model to a string format within YAML, set the title to "ArtifactModel" and the type to "object" for clarity and consistency.

```yaml
type: object
properties:
  field_name:
    type: string
    description: "Description of the field."
  another_field:
    type: number
    description: "Description for a numeric field."
  list_field:
    type: array
    items:
      type: string
    description: "Description for a list field."
required:
  - field_name
  - another_field
  - list_field
```

