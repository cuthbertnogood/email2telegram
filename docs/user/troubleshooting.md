# Troubleshooting

## `AUTHENTICATIONFAILED` / invalid credentials

Check:

- Use Yandex app password, not browser password.
- `IMAP_USER` is a full email address.
- Host is `imap.yandex.com` or `imap.yandex.ru`.
- `.env` has no accidental spaces.
- Active Python is inside `.venv`.

Recreate venv if needed:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## No new messages in Telegram

- Verify `TELEGRAM_CHAT_ID` is included in `TELEGRAM_ALLOWED_CHAT_IDS`.
- Ensure `IMAP_MAILBOX` points to the folder where new emails arrive.
- Inspect logs: `docker compose -f docker-compose.hub.yml logs -f` (VPS) or `python src/main.py` locally.

## Check IMAP visibility quickly

```bash
python src/imap_probe.py --last 5
```

## Bot Token Leaked (in Logs / Support Tickets)

`docker compose logs` for python-telegram-bot shows raw URLs like `api.telegram.org/bot<TOKEN>/sendMessage`. If you pasted that anywhere, treat the token as compromised.

Rotation (from your PC only):

1. @BotFather → `/revoke` → `/newtoken` → copy the new token.
2. Edit `TELEGRAM_BOT_TOKEN=` in **local `.env`**.
3. Run `./scripts/release.sh`. The filtered `.env` is pushed to VPS, the container is recreated, the new token is live.

Prevention: never paste raw logs that contain Telegram API URLs. Strip the URL or mask everything between `/bot` and `/` (the token) before sharing. See [deploy.md](deploy.md#rotating-secrets-bot-token-imap-password) for details.
