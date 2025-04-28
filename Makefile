DATA?="${PWD}"
DOCKER_FILE=Dockerfile
NAME?=codebase_analysis
WORKING_DIR=/workspace

build_image:
	docker build -t $(NAME) -f $(DOCKER_FILE) .

bash: build_image
	docker run --rm --net=host -it -w $(WORKING_DIR) --shm-size=10.07gb -v $(DATA):/workspace -v $(DATA)/..:/coding-projects $(NAME) bash

embedding:
	docker run \
	--rm \
	-p 8080:80 \
	--name tei_endpoint \
	ghcr.io/huggingface/text-embeddings-inference:cpu-latest \
	--model-id infly/inf-retriever-v1-1.5b