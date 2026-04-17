# CI Workflows

## `ci.yml`

- Trigger: all pushes and pull requests.
- Runs Python 3.12 tests: `pytest -q`.

## `docker-publish.yml`

- Trigger: manual dispatch or tag push `v*`.
- Builds and pushes multi-arch image to Docker Hub.
- Uses `VERSION` for `APP_VERSION` build-arg and one tag.

## `readme-sync.yml`

- Trigger: changes to `README.md` or `README.ru.md`.
- Runs `python3 scripts/sync_readme_ru.py --check`.
- Fails if Russian README marker hash does not match current English README.
