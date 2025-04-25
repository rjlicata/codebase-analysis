DATA?="${PWD}"
DOCKER_FILE=Dockerfile
NAME?=codebase_analysis
WORKING_DIR=/workspace

build_image:
	docker build -t $(NAME) -f $(DOCKER_FILE) .

bash: build_image
	docker run --rm -it -w $(WORKING_DIR) --shm-size=10.07gb -v $(DATA):/workspace $(NAME) bash
