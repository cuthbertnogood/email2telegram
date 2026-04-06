# From your PC to the VPS (Docker Hub stack)

This guide covers `**scripts/host_to_vps.sh**`: copy `docker-compose.hub.yml` and `deploy/*` helpers to the server over **SSH/scp**, optionally run `**docker compose pull`** / `**up**` remotely, and enable the **systemd Hub pull timer**.

Pair with **[host-to-docker-hub.md](host-to-docker-hub.md)** to publish the image, then **[DEPLOY.md](../DEPLOY.md)** for the full VPS checklist.

---

## Prerequisites

- **SSH** access to the VPS as a user that can run `**docker compose`** (often after `usermod -aG docker`).
- **OpenSSH client** on your PC (`ssh`, `scp`).
- Run commands from **any directory**; the script changes to the repository root automatically.

---

## Configuration (`.env` in repo root)


| Variable          | Required                                              | Description                                                 |
| ----------------- | ----------------------------------------------------- | ----------------------------------------------------------- |
| `VPS_USER`        | Yes (unless you pass `user@host` on the command line) | SSH username.                                               |
| `VPS_HOST`        | Yes (same)                                            | Hostname or IP.                                             |
| `VPS_SSH_PORT`    | No                                                    | SSH port if not 22; or use `-p PORT` before the subcommand. |
| `VPS_REMOTE_DIR`  | No                                                    | Remote directory (default `/opt/email2telegram`).           |
| `VPS_SSH_OPTS`    | No                                                    | Extra `ssh`/`scp` arguments, e.g. `-i ~/.ssh/key`.          |
| `VPS_SSH_VERBOSE` | No                                                    | Set to `1` to add `ssh -v` for debugging.                   |


The script **sources** `.env` before reading these values.

**Shell wins:** if `VPS_USER`, `VPS_HOST`, etc. are already exported before you run the script, the script restores those values after sourcing `.env` (same pattern as `host_to_docker_hub.sh` for `DOCKER_USER`).

See also **[.env.example](../.env.example)**.

---

## What the script copies (`sync`)

Into `VPS_REMOTE_DIR` on the server:

- `docker-compose.hub.yml`
- `deploy/vps-update-hub.sh`
- `deploy/email2telegram.service`
- `deploy/email2telegram-hub-update.service`
- `deploy/email2telegram-hub-update.timer`

You still maintain `**.env` on the VPS** separately (secrets, `DOCKER_IMAGE`). The script prints a short reminder after `sync`.

---

## Subcommands


| Command          | Purpose                                                                                                  |
| ---------------- | -------------------------------------------------------------------------------------------------------- |
| `sync`           | `scp` the files listed above.                                                                            |
| `pull-up`        | SSH: `docker compose -f docker-compose.hub.yml pull` then `up -d --force-recreate`.                      |
| `enable-timer`   | Copy Hub timer units to `/etc/systemd/system/` and `enable --now` (may prompt for `sudo` over SSH `-t`). |
| `deploy`         | `sync`, then `pull-up`, then `enable-timer` (first-time Hub path from PC).                               |
| `hub-checklist`  | Print Docker Hub browser + PAT + link to `host_to_docker_hub.sh`.                                        |
| `install-docker` | Print Ubuntu Docker install hints (run on the VPS).                                                      |
| `systemd-hints`  | Print optional `email2telegram.service` / timer copy commands.                                           |


Remote `docker` runs under `**bash -lc`** so `docker compose` is on `PATH` like an interactive login.

---

## Run

From the repo root:

```bash
./scripts/host_to_vps.sh sync
./scripts/host_to_vps.sh pull-up
./scripts/host_to_vps.sh deploy    # first-time: sync + pull-up + timer
```

Non-default SSH port:

```bash
./scripts/host_to_vps.sh -p 2222 sync
```

Override `.env` target for one run:

```bash
./scripts/host_to_vps.sh sync deploy@203.0.113.10 /srv/bot
```

### Help

```bash
./scripts/host_to_vps.sh --help
```

---

## Troubleshooting


| Issue                            | What to check                                                                                                     |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `set VPS_USER and VPS_HOST`      | Fill `.env` or pass `user@host` as the first argument after the subcommand.                                       |
| `Connection closed` after `sync` | `VPS_SSH_VERBOSE=1 ./scripts/host_to_vps.sh pull-up` — on the VPS, `docker compose version` as the same SSH user. |
| Permission denied on `scp`       | Remote dir exists and is writable; see the `sudo mkdir` / `chown` tip printed by `sync`.                          |
| `sudo` over SSH                  | `enable-timer` and `deploy` use `ssh -t` for `sudo`; agent forwarding / NOPASSWD depends on your server setup.    |


---

## Related docs

- **[DEPLOY.md](../DEPLOY.md)** — full VPS deploy flow, firewall, operations.
- **[host-to-docker-hub.md](host-to-docker-hub.md)** — build and push the image.
- **[docker-vps-architecture.md](docker-vps-architecture.md)** — components and diagrams.

