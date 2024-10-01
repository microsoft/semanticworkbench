ARG python_image=python:3.11-slim

FROM ${python_image} AS build

RUN apt-get update && \
    apt-get install -y gcc git

RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH

RUN pip3 install --no-cache-dir --upgrade pip

# copy the directory structure so the relative paths remain the same
COPY ./semantic-workbench-assistants/skill-assistant /packages/semantic-workbench-assistants/skill-assistant
COPY ./semantic-workbench/v1/service/semantic-workbench-api-model /packages/semantic-workbench/v1/service/semantic-workbench-api-model
COPY ./semantic-workbench/v1/service/semantic-workbench-assistant /packages/semantic-workbench/v1/service/semantic-workbench-assistant
COPY ./skills/skill-library /packages/skills/skill-library
COPY ./skills/skills /packages/skills/skills
COPY ./libraries/chat-driver /packages/libraries/chat-driver
COPY ./libraries/content-safety-evaluators/azure-content-safety-evaluator /packages/libraries/content-safety-evaluators/azure-content-safety-evaluator
COPY ./libraries/content-safety-evaluators/openai-content-safety-evaluator /packages/libraries/content-safety-evaluators/openai-content-safety-evaluator
COPY ./libraries/context /packages/libraries/context
COPY ./libraries/events /packages/libraries/events
COPY ./libraries/function-registry /packages/libraries/function-registry

RUN pip3 install --no-cache-dir /packages/semantic-workbench-assistants/skill-assistant

FROM ${python_image}

COPY --from=build /venv /venv
ENV PATH=/venv/bin:$PATH

ENTRYPOINT ["start-semantic-workbench-assistant", "assistant.skill_assistant:app", "--host", "0.0.0.0"]
