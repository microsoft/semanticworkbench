repo_root = $(shell git rev-parse --show-toplevel)
mkfile_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))

# the directory containing the mcp-servers's Makefile is expected to be
# the directory of the mcp-server
invoking_makefile_directory = $(notdir $(patsubst %/,%,$(dir $(realpath $(firstword $(MAKEFILE_LIST))))))

MCP_SERVER_PACKAGE ?= $(invoking_makefile_directory)
MCP_SERVER_IMAGE_NAME ?= $(subst -,_,$(invoking_makefile_directory))
MCP_SERVER_MAIN_MODULE ?= $(MCP_SERVER_IMAGE_NAME).start

DOCKER_PATH = $(repo_root)
DOCKER_FILE = $(repo_root)/tools/docker/Dockerfile.mcp-server
DOCKER_BUILD_ARGS = main_module=$(MCP_SERVER_MAIN_MODULE) package=$(MCP_SERVER_PACKAGE)
DOCKER_IMAGE_NAME = $(MCP_SERVER_IMAGE_NAME)

AZURE_WEBSITE_NAME ?= $(MCP_SERVER_PACKAGE)-service

include $(mkfile_dir)/docker.mk

docker-run-local: docker-build
	docker run --rm -it --add-host=host.docker.internal:host-gateway $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)
