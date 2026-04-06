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

# --- Docker Hub: DOCKER_USER in shell, or in .env (see .env.example) ---
TAG ?= latest

hub-login:
	@if [ -n "$(DOCKER_USER)" ]; then docker login -u "$(DOCKER_USER)"; else docker login; fi

# Delegates to scripts/host_to_docker_hub.sh (MINOR bump in script unless NO_BUMP=1).
hub-build:
	DOCKER_USER=$(DOCKER_USER) TAG=$(TAG) ./scripts/host_to_docker_hub.sh

# Pushes are done inside hub-build (buildx --push). Kept as an alias for existing docs.
hub-push: hub-build

# On VPS with docker-compose.hub.yml + DOCKER_IMAGE in .env
vps-pull:
	docker compose -f docker-compose.hub.yml pull && docker compose -f docker-compose.hub.yml up -d --force-recreate
