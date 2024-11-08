repo_root = $(shell git rev-parse --show-toplevel)

include $(repo_root)/tools/makefiles/python.mk

-include ./.env

DBTYPE ?= sqlite

ifeq ($(DBTYPE), postgresql)
WORKBENCH__DB__URL ?= postgresql:///workbench
else
WORKBENCH__DB__URL ?= sqlite:///.data/workbench.db
endif

.PHONY: start
start:
	WORKBENCH__DB__URL="$(WORKBENCH__DB__URL)" uv run start-semantic-workbench-service

.PHONY: alembic-upgrade-head
alembic-upgrade-head:
	WORKBENCH__DB__URL="$(WORKBENCH__DB__URL)" uv run alembic upgrade head

.PHONY: alembic-generate-migration
alembic-generate-migration:
ifndef migration
	$(info You must provide a name for the migration.)
	$(info ex: make alembic-generate-migration migration="neato changes")
	$(error "migration" is not set)
else
	WORKBENCH__DB__URL="$(WORKBENCH__DB__URL)" uv run alembic revision --autogenerate -m "$(migration)"
endif

DOCKER_PATH = $(repo_root)

docker-%: DOCKER_IMAGE_NAME := workbench

include $(repo_root)/tools/makefiles/docker.mk
