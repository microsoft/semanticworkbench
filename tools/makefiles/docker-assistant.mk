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

include $(this_dir)/docker.mk
