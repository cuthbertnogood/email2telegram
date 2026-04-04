.PHONY: up down logs build pull hub-login hub-build hub-push vps-pull

# Local dev (build from Dockerfile)
up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

# Git pull + rebuild (local dev on server with full repo)
pull:
	git pull && docker compose up -d --build

# --- Docker Hub (set DOCKER_USER to your hub username) ---
DOCKER_USER ?= yourdockerhub
IMAGE ?= $(DOCKER_USER)/email2telegram
TAG ?= latest
GIT_SHA := $(shell git rev-parse --short HEAD 2>/dev/null || echo local)

hub-login:
	docker login -u $(DOCKER_USER)

hub-build:
	docker build -t $(IMAGE):$(TAG) -t $(IMAGE):$(GIT_SHA) .

hub-push: hub-build
	docker push $(IMAGE):$(TAG)
	docker push $(IMAGE):$(GIT_SHA)

# On VPS with docker-compose.hub.yml + DOCKER_IMAGE in .env
vps-pull:
	docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d
