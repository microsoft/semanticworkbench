repo_root = $(shell git rev-parse --show-toplevel)

.DEFAULT_GOAL := venv

include $(repo_root)/tools/makefiles/poetry.mk

include $(repo_root)/tools/makefiles/docker.mk

DOCKER_PATH = $(repo_root)

DOCKER_IMAGE_NAME := skill_assistant
