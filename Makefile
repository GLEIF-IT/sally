.PHONY: build-sally
build-sally:
	@docker buildx build --platform=linux/amd64 --no-cache -f containers/sally.dockerfile --tag gleif/sally:0.8.0 .
	@docker buildx build --platform=linux/arm64 --no-cache -f containers/sally-arm64.dockerfile --tag gleif/sally:0.8.0-arm64 .

.PHONY: run-sally
run-agent:
	@docker run -p 5921:5921 -p 5923:5923 --name agent gleif/sally:0.8.0

.PHONY: push-all
push-all:
	@docker push gleif/sally --all-tags
