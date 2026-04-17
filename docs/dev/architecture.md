# Architecture

The service is a single containerized process that polls IMAP and forwards text to Telegram.
No inbound ports are exposed.

## Runtime Components

- Docker Engine + Compose on VPS.
- App container (`python src/main.py`).
- Persistent volume `email2telegram_data` mounted to `/data`.
- Optional systemd timer for periodic image refresh from Docker Hub.

## Data Flow

```mermaid
sequenceDiagram
  participant JQ as JobQueue
  participant Pipeline as run_delivery_cycle
  participant IMAP as ImapClient
  participant Telegram as BotAPI
  participant State as StateStore
  loop every POLL_INTERVAL_SECONDS
    JQ->>Pipeline: _poll_imap
    Pipeline->>IMAP: fetch_new_messages
    IMAP-->>Pipeline: raw messages
    Pipeline->>Telegram: send formatted text
    Pipeline->>State: update last_seen_uid and dedup keys
  end
```

## Deploy Topology

```mermaid
flowchart TB
  subgraph vpsHost [VPSHost]
    compose[DockerCompose]
    ctr[email2telegramContainer]
    vol[(email2telegram_data)]
    compose --> ctr
    ctr --> vol
  end
  hub[DockerHub] -->|pull image| compose
  imap[IMAPServer] <-->|outbound TLS| ctr
  tg[TelegramAPI] <-->|outbound polling and send| ctr
```
