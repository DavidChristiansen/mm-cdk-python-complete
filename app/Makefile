.PHONY: docker

docker:
	docker build . -t "$(shell aws sts get-caller-identity --output text --query Account ).dkr.ecr.$(AWS_DEFAULT_REGION).amazonaws.com/mythicalmysfits/service:latest"

push:
	$(shell aws ecr get-login --no-include-email)
	docker push "$(shell aws sts get-caller-identity --output text --query Account ).dkr.ecr.$(AWS_DEFAULT_REGION).amazonaws.com/mythicalmysfits/service:latest"
