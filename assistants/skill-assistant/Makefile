repo_root = $(shell git rev-parse --show-toplevel)

.DEFAULT_GOAL := venv

include $(repo_root)/build-tools/makefiles/poetry.mk

DOCKER_REGISTRY_NAME = acrsemanticworkbench
DOCKER_PATH = $(repo_root)

docker-%: DOCKER_IMAGE_NAME = skill_assistant
docker-%: DOCKER_FILE = Dockerfile
docker-build: .docker-build
docker-push: .docker-push
docker-deploy: AZURE_WEBSITE_NAME = skill-assistant-service
docker-deploy: .azure-container-deploy

include $(repo_root)/build-tools/makefiles/docker.mk
