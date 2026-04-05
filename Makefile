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
TAG ?= latest

hub-login:
	docker login -u $(DOCKER_USER)

# Delegates to scripts/docker-hub-publish.sh (always runs bump_docker_minor.py).
hub-build:
	DOCKER_USER=$(DOCKER_USER) TAG=$(TAG) ./scripts/docker-hub-publish.sh

# Pushes are done inside hub-build (buildx --push). Kept as an alias for existing docs.
hub-push: hub-build

# On VPS with docker-compose.hub.yml + DOCKER_IMAGE in .env
vps-pull:
	docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d --force-recreate
