# Guided Conversation

This library is a modified copy of the [guided-conversation](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/demos/guided_conversations) library from the [Semantic Kernel](https://github.com/microsoft/semantic-kernel) repository.

The guided conversation library supports scenarios where an agent with a goal and constraints leads a conversation. There are many of these scenarios where we hold conversations that are driven by an objective and constraints. For example:

- a teacher guiding a student through a lesson
- a call center representative collecting information about a customer's issue
- a sales representative helping a customer find the right product for their specific needs
- an interviewer asking candidate a series of questions to assess their fit for a role
- a nurse asking a series of questions to triage the severity of a patient's symptoms
- a meeting where participants go around sharing their updates and discussing next steps

The common thread between all these scenarios is that they are between a creator leading the conversation and a user(s) who are participating. The creator defines the goals, a plan for how the conversation should flow, and often collects key information through a form throughout the conversation. They must exercise judgment to navigate and adapt the conversation towards achieving the set goal all while writing down key information and planning in advance.

The goal of this framework is to show how we can build a common framework to create AI agents that can assist a creator in running conversational scenarios semi-autonomously and generating artifacts like notes, forms, and plans that can be used to track progress and outcomes. A key tenant of this framework is the following principal: think with the model, plan with the code. This means that the model is used to understand user inputs and make complex decisions, but code is used to apply constraints and provide structure to make the system reliable. To better understand this concept, please visit the original project on the [Semantic Kernel](https://github.com/microsoft/semantic-kernel) repository and their [guided-conversation](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/demos/guided_conversations) library, notebooks, demos, and documentation.

## Example usage with a Semantic Workbench assistant

For an example of how to use this library with a Semantic Workbench assistant, we have provided a [Guided Conversation Assistant](../../../assistants/guided-conversation-assistant/) for reference.
