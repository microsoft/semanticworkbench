repo_root = $(shell git rev-parse --show-toplevel)

.DEFAULT_GOAL := venv

include $(repo_root)/tools/makefiles/poetry.mk

test: venv
	$(VENV_BIN)/pytest

WORKBENCH__DB__URL ?= postgresql:///workbench

.PHONY: alembic-upgrade-head
alembic-upgrade-head:
	cd semantic-workbench-service \
	&& WORKBENCH__DB__URL="$(WORKBENCH__DB__URL)" alembic upgrade head

.PHONY: alembic-generate-migration
alembic-generate-migration:
ifndef migration
	$(info You must provide a name for the migration.)
	$(info ex: make alembic-generate-migration migration="neato changes")
	$(error "migration" is not set)
else
	cd semantic-workbench-service \
	&& WORKBENCH__DB__URL="$(WORKBENCH__DB__URL)" alembic revision --autogenerate -m "$(migration)"
endif

DOCKER_REGISTRY_NAME = acrsemanticworkbench

docker-%-workbench: DOCKER_IMAGE_NAME := workbench
docker-%-workbench: DOCKER_FILE := Dockerfile.workbench
docker-%-workbench: AZURE_WEBSITE_NAME := semantic-workbench-service
docker-build-workbench: .docker-build
docker-push-workbench: .docker-push
docker-deploy-workbench: .azure-container-deploy

include $(repo_root)/tools/makefiles/docker.mk
