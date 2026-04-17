# Telegram Setup

Required variables:

- `TELEGRAM_BOT_TOKEN`: token from BotFather
- `TELEGRAM_CHAT_ID`: destination chat for forwarded mail
- `TELEGRAM_ALLOWED_CHAT_IDS`: comma-separated allowlist; must include `TELEGRAM_CHAT_ID`

Behavior:

- Mail is delivered only to `TELEGRAM_CHAT_ID` if that chat is in allowlist.
- `/start` is handled only for chats in allowlist.
- Other chats receive no response.
