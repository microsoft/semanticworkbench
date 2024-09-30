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

# all assistants use the same dockerfile
docker-%-assistant: DOCKER_FILE := Dockerfile.assistant

ASSISTANT_EXAMPLES = openai_chat autogen_chat gemini_chat

define assistant_targets
docker-%-$(subst _,-,$(1))-assistant: DOCKER_BUILD_ARGS := --build-arg assistant_app_name=semantic_workbench_assistant_examples.$(1):app
docker-%-$(subst _,-,$(1))-assistant: DOCKER_IMAGE_NAME := $(1)
docker-%-$(subst _,-,$(1))-assistant: AZURE_WEBSITE_NAME := $(subst _,-,$(1))-assistant-service
docker-build-$(subst _,-,$(1))-assistant: .docker-build
docker-push-$(subst _,-,$(1))-assistant: .docker-push
docker-deploy-$(subst _,-,$(1))-assistant: .azure-container-deploy
endef

$(foreach example,$(ASSISTANT_EXAMPLES),$(eval $(call assistant_targets,$(example))))

docker-build-assistants:
	@$(foreach example,$(ASSISTANT_EXAMPLES),$(MAKE) docker-build-$(subst _,-,$(example))-assistant;)

docker-push-assistants:
	@$(foreach example,$(ASSISTANT_EXAMPLES),$(MAKE) docker-push-$(subst _,-,$(example))-assistant;)

docker-deploy-assistants:
	@$(foreach example,$(ASSISTANT_EXAMPLES),$(MAKE) docker-deploy-$(subst _,-,$(example))-assistant;)

include $(repo_root)/tools/makefiles/docker.mk
