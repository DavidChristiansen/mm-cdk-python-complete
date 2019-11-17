.PHONY: docker push user-pool user-pool-client

docker:
	docker build . -t "$(shell aws sts get-caller-identity --output text --query Account ).dkr.ecr.$(AWS_DEFAULT_REGION).amazonaws.com/mythicalmysfits/service:latest"

push:
	$(shell aws ecr get-login --no-include-email)
	docker push "$(shell aws sts get-caller-identity --output text --query Account ).dkr.ecr.$(AWS_DEFAULT_REGION).amazonaws.com/mythicalmysfits/service:latest"

dynamodb:
	aws dynamodb batch-write-item --request-items file://data/populate-dynamodb.json

user-pool:
	./safe-make-user-pool.sh

user-pool-client:
	./safe-make-user-pool-client.sh
