# Yandex IMAP Setup

1. Open [Yandex ID Security](https://id.yandex.ru/security) for the mailbox account.
2. Create an app password in "Application passwords".
3. Put that value into `IMAP_PASS` in `.env`.
4. Set `IMAP_USER` to the full email address.

Recommended IMAP values:

- `IMAP_HOST=imap.yandex.com`
- `IMAP_PORT=993`

Fallback host if login fails:

- `imap.yandex.ru`

If available in account settings, enable IMAP access for mail clients.
