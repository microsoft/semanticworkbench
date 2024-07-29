DOCKER_REGISTRY_NAME ?=
DOCKER_REGISTRY_HOST ?= $(DOCKER_REGISTRY_NAME).azurecr.io
DOCKER_USERNAME ?= $(DOCKER_REGISTRY_NAME)
DOCKER_IMAGE_TAG ?= $(shell git rev-parse HEAD)
DOCKER_PUSH_LATEST ?= true
DOCKER_PATH ?= .
DOCKER_ARGS ?=
DOCKER_BUILD_ARGS ?=


AZURE_WEBSITE_NAME ?=
AZURE_WEBSITE_SLOT ?= staging
AZURE_WEBSITE_TARGET_SLOT ?= production
AZURE_WEBSITE_SUBSCRIPTION ?= 8a673afb-d858-4a97-a490-2625396d1484
AZURE_WEBSITE_RESOURCE_GROUP ?= rg-semantic-workbench

require_value = $(foreach var,$(1),$(if $(strip $($(var))),,$(error "Variable $(var) is not set: $($(var))")))

.PHONY: .docker-build
.docker-build:
	$(call require_value,DOCKER_IMAGE_NAME DOCKER_IMAGE_TAG DOCKER_FILE DOCKER_PATH)
	docker $(DOCKER_ARGS) build -t $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) $(DOCKER_BUILD_ARGS) $(DOCKER_PATH) -f $(DOCKER_FILE)

.PHONY: .docker-push
.docker-push: .docker-build
	$(call require_value,DOCKER_REGISTRY_NAME DOCKER_REGISTRY_HOST DOCKER_IMAGE_NAME DOCKER_IMAGE_TAG)
ifndef DOCKER_PASSWORD
	az acr login --name $(DOCKER_REGISTRY_NAME)
else
	@ echo "$(DOCKER_PASSWORD)" | docker login $(DOCKER_REGISTRY_HOST) --username $(DOCKER_USERNAME) --password-stdin
endif
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) $(DOCKER_REGISTRY_HOST)/$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)
	docker push $(DOCKER_REGISTRY_HOST)/$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)
ifeq ($(DOCKER_PUSH_LATEST),true)
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) $(DOCKER_REGISTRY_HOST)/$(DOCKER_IMAGE_NAME)
	docker push $(DOCKER_REGISTRY_HOST)/$(DOCKER_IMAGE_NAME)
endif

define update-container
	az webapp config container set \
		--subscription $(AZURE_WEBSITE_SUBSCRIPTION) \
		--resource-group $(AZURE_WEBSITE_RESOURCE_GROUP) \
		--name $(1) --slot $(AZURE_WEBSITE_SLOT) \
		--container-image-name $(DOCKER_REGISTRY_HOST)/$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)

endef

define swap-slots
	az webapp deployment slot swap \
		--subscription $(AZURE_WEBSITE_SUBSCRIPTION) \
		--resource-group $(AZURE_WEBSITE_RESOURCE_GROUP) \
		--name $(1) \
		--slot $(AZURE_WEBSITE_SLOT) \
		--target-slot $(AZURE_WEBSITE_TARGET_SLOT) \
		--verbose

endef

.PHONY: .azure-container-deploy
.azure-container-deploy:
	$(call require_value,AZURE_WEBSITE_SUBSCRIPTION AZURE_WEBSITE_NAME AZURE_WEBSITE_SLOT AZURE_WEBSITE_RESOURCE_GROUP DOCKER_REGISTRY_HOST DOCKER_IMAGE_NAME DOCKER_IMAGE_TAG)
	$(foreach website_name,$(AZURE_WEBSITE_NAME),$(call update-container,$(website_name)))
ifneq ($(AZURE_WEBSITE_SLOT),$(AZURE_WEBSITE_TARGET_SLOT))
	$(foreach website_name,$(AZURE_WEBSITE_NAME),$(call swap-slots,$(website_name)))
endif
