repo_root = $(shell git rev-parse --show-toplevel)
this_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))

# the directory containing the assistant's Makefile is expected to be
# the directory of the assistant
invoking_makefile_directory = $(notdir $(patsubst %/,%,$(dir $(realpath $(firstword $(MAKEFILE_LIST))))))

ASSISTANT_APP ?= assistant:app
ASSISTANT_PACKAGE ?= $(invoking_makefile_directory)
ASSISTANT_IMAGE_NAME ?= $(subst -,_,$(invoking_makefile_directory))

DOCKER_PATH = $(repo_root)
DOCKER_FILE = $(repo_root)/tools/docker/Dockerfile.assistant
DOCKER_BUILD_ARGS = app=$(ASSISTANT_APP) package=$(ASSISTANT_PACKAGE)
DOCKER_IMAGE_NAME = $(ASSISTANT_IMAGE_NAME)

AZURE_WEBSITE_NAME ?= $(ASSISTANT_PACKAGE)-service

include $(this_dir)/docker.mk


ASSISTANT__WORKBENCH_SERVICE_URL ?= http://host.docker.internal:3000

docker-run-local: docker-build
	docker run --rm -it --add-host=host.docker.internal:host-gateway --env assistant__workbench_service_url=$(ASSISTANT__WORKBENCH_SERVICE_URL) $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)
