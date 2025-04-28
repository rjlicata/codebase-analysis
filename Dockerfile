FROM python:3.12.9

WORKDIR /tmp
COPY src/ ./src
COPY pyproject.toml/ ./pyproject.toml

RUN pip install .

WORKDIR /workspace

ENTRYPOINT /bin/bash