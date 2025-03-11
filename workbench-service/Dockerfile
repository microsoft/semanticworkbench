ARG python_image=python:3.11-slim

FROM ${python_image} AS build

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY ./libraries/python/semantic-workbench-api-model /libraries/python/semantic-workbench-api-model
COPY ./libraries/python/semantic-workbench-assistant /libraries/python/semantic-workbench-assistant
COPY ./workbench-service /workbench-service

RUN uv sync --directory /workbench-service --no-editable --no-dev --locked

FROM ${python_image}

# BEGIN: enable ssh in azure web app - comment out if not needed
########
# install sshd and set password for root
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    && rm -rf /var/lib/apt/lists/* \
    && echo "root:Docker!" | chpasswd

# azure sshd config
COPY ./tools/docker/azure_website_sshd.conf /etc/ssh/sshd_config
ENV SSHD_PORT=2222
########
# END: enable ssh in azure web app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /workbench-service/.venv /workbench-service/.venv
ENV PATH=/workbench-service/.venv/bin:$PATH

# alembic migrations related files
COPY ./workbench-service/alembic.ini /workbench-service/alembic.ini
COPY ./workbench-service/migrations /workbench-service/migrations

# entrypoint script
COPY ./tools/docker/docker-entrypoint.sh /scripts/docker-entrypoint.sh
RUN chmod +x /scripts/docker-entrypoint.sh

WORKDIR /workbench-service

ENV workbench__service__host=0.0.0.0
ENV workbench__service__port=3000

SHELL ["/bin/bash", "-c"]
ENTRYPOINT ["/scripts/docker-entrypoint.sh"]
CMD ["start-service"]
