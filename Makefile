.PHONY: build-kara
build-kara:
	@docker buildx build --platform=linux/amd64 --no-cache -f containers/kara.dockerfile --tag gleif/kara:latest --tag gleif/kara:0.1.0 .

.PHONY: run-kara
run-agent:
	@docker run -p 5921:5921 -p 5923:5923 --name agent gleif/kara:0.1.0

.PHONY: push-all
push-all:
	@docker push gleif/kara --all-tags
