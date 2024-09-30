ARG python_image=python:3.11-slim

FROM ${python_image} AS build

RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH

RUN pip3 install --no-cache-dir --upgrade pip

COPY ./libraries/python/semantic-workbench-api-model /packages/libraries/python/semantic-workbench-api-model
COPY ./workbench-service /packages/workbench-service

RUN pip3 install --no-cache-dir /packages/workbench-service

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

COPY --from=build /venv /venv
ENV PATH=/venv/bin:$PATH

# alembic migrations related files
COPY ./workbench-service/alembic.ini /workbench-service/alembic.ini
COPY ./workbench-service/migrations /workbench-service/migrations

# entrypoint script
COPY ./tools/docker/docker-entrypoint.sh /scripts/docker-entrypoint.sh
RUN chmod +x /scripts/docker-entrypoint.sh

WORKDIR /workbench-service

SHELL ["/bin/bash", "-c"]
ENTRYPOINT ["/scripts/docker-entrypoint.sh"]
CMD ["start-semantic-workbench-service"]
