.PHONY: build-sally

VERSION=1.0.0-rc1
REGISTRY=gleif
IMAGE=sally
IMAGE_TAG=$(REGISTRY)/$(IMAGE):latest
VERSIONED_TAG=$(REGISTRY)/$(IMAGE):$(VERSION)

define DOCKER_WARNING
In order to use the multi-platform build enable the containerd image store
The containerd image store is not enabled by default.
To enable the feature for Docker Desktop:
	Navigate to Settings in Docker Desktop.
	In the General tab, check Use containerd for pulling and storing images.
	Select Apply and Restart."
endef

build-sally: .warn
	@docker build \
		--platform=linux/amd64,linux/arm64 \
		-f containers/sally.dockerfile \
		-t $(VERSIONED_TAG) \
		-t $(IMAGE_TAG) .

.PHONY: run-sally
run-agent:
	@docker run -p 5921:5921 -p 5923:5923 --name agent $(VERSIONED_TAG)

.PHONY: push-all
publish-sally:
	@docker push $(VERSIONED_TAG)
	@docker push $(IMAGE_TAG)

.warn:
	@echo -e ${RED}"$$DOCKER_WARNING"${NO_COLOUR}

RED="\033[0;31m"
NO_COLOUR="\033[0m"
export DOCKER_WARNING