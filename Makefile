DATA?="${PWD}"
DOCKER_FILE=Dockerfile
NAME?=codebase_analysis
WORKING_DIR=/workspace

build_image:
	docker build -t $(NAME) -f $(DOCKER_FILE) .

network:
	docker network create codebase_network

embedding:
	docker run \
	--rm \
	-p 8080:80 \
	--name tei_endpoint \
	ghcr.io/huggingface/text-embeddings-inference:cpu-latest \
	--model-id infly/inf-retriever-v1-1.5b

postgres:
	docker run \
	--rm \
	-d \
	--net=codebase_network \
	--name postgres \
	-e POSTGRES_USER=postgres \
	-e POSTGRES_PASSWORD=postgres \
	-e POSTGRES_DB=codebase \
	-p 5432:5432 \
	-v $(DATA)/db/codebase:/var/lib/postgresql/data \
	pgvector/pgvector:pg17

enter_psql:
	docker exec -it postgres psql -U postgres -d codebase

app: build_image
	docker run --rm  --net=codebase_network -p 8501:8501 -w $(WORKING_DIR) --shm-size=10.07gb -v $(DATA):/workspace $(NAME)