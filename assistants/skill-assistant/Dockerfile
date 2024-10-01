ARG python_image=python:3.11-slim

FROM ${python_image} AS build

RUN apt-get update && \
    apt-get install -y gcc git

RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH

RUN pip3 install --no-cache-dir --upgrade pip


# copy the directory structure so the relative paths remain the same

# semantic workbench packages
COPY ./libraries/python/semantic-workbench-api-model /packages/libraries/python/semantic-workbench-api-model
COPY ./libraries/python/semantic-workbench-assistant /packages/libraries/python/semantic-workbench-assistant

# content safety
COPY ./libraries/python/content-safety /packages/libraries/python/content-safety

# skills
COPY ./libraries/python/chat-driver /packages/libraries/python/chat-driver
COPY ./libraries/python/context /packages/libraries/python/context
COPY ./libraries/python/events /packages/libraries/python/events
COPY ./libraries/python/function-registry /packages/libraries/python/function-registry
COPY ./libraries/python/skills/skill-library /packages/libraries/python/skills/skill-library
COPY ./libraries/python/skills/skills /packages/libraries/python/skills/skills

# this assistant package
COPY ./assistants/skill-assistant/ /packages/assistants/skill-assistant

# install the assistant package dependencies - ensure the path matches the path in the COPY command above
RUN pip3 install --no-cache-dir /packages/assistants/skill-assistant


FROM ${python_image}

COPY --from=build /venv /venv
ENV PATH=/venv/bin:$PATH

ENTRYPOINT ["start-semantic-workbench-assistant", "assistant.skill_assistant:app", "--host", "0.0.0.0"]
