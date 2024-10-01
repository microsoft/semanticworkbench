ARG python_image=python:3.11-slim

FROM ${python_image} AS build

# RUN apt-get update && \
#     apt-get install -y gcc git

RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH

RUN pip3 install --no-cache-dir --upgrade pip

# copy the directory structure so the relative paths remain the same

# semantic workbench packages
COPY ./libraries/python/semantic-workbench-api-model /packages/libraries/python/semantic-workbench-api-model
COPY ./libraries/python/semantic-workbench-assistant /packages/libraries/python/semantic-workbench-assistant

# content safety
COPY ./libraries/python/content-safety /packages/libraries/python/content-safety

# this assistant package
COPY ./assistants/prospector-assistant/ /packages/assistants/prospector-assistant

# install the assistant package dependencies - ensure the path matches the path in the COPY command above
RUN pip3 install --no-cache-dir /packages/assistants/prospector-assistant

FROM ${python_image}

COPY --from=build /venv /venv
ENV PATH=/venv/bin:$PATH

ENV host="0.0.0.0"
ENV port="3001"

# container debugging
#CMD python -m debugpy --listen 0.0.0.0:5678 --wait-for-client start-semantic-workbench-assistant assistant.chat:app --host ${host} --port ${port}

# container entrypoint, start the assistant - defaults to the `app` FastAPI object in the `assistant.chat` module
# if you have a different FastAPI object, module name, or path, update the entrypoint accordingly
ENTRYPOINT start-semantic-workbench-assistant assistant.chat:app --host ${host} --port ${port}
