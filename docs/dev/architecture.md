# Architecture

The service is a single containerized process that polls IMAP and forwards text to Telegram.
No inbound ports are exposed.

## Module responsibilities (`src/`)

| Module | Role |
|--------|------|
| `main.py` | Process entry: `python-telegram-bot` app, `JobQueue`, command handlers, wires IMAP polling → `run_delivery_cycle`, allowlist enforcement. |
| `imap_client.py` | IMAP connection and fetch; blocking I/O called from async via `asyncio.to_thread`. |
| `parser.py` | Parse raw RFC822 bytes into structured fields for the pipeline. |
| `pipeline.py` | `run_delivery_cycle`: orchestrate fetch, dedup, format, Telegram send, state updates. |
| `telegram_client.py` | Send formatted chunks to Telegram (chunking / API details). |
| `message_format.py` | Plain-text email formatting and `split_for_telegram` limits. |
| `allowlist.py` | Parse and represent allowed chat IDs; used by handlers and sender. |
| `state.py` | Persistent cursor / dedup store (`StateStore`, file under `STATE_FILE`). |
| `imap_probe.py` | Standalone IMAP connectivity and mailbox preview (no Telegram). |
| `version.py` | Version string / banner for logs and Telegram. |

Imports between `src/` modules use **no** `src.` prefix (entrypoint is `python src/main.py` with `src` on the path).

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
