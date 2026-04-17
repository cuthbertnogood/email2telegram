#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_EN = ROOT / "README.md"
README_RU = ROOT / "README.ru.md"
MARKER_RE = re.compile(r"<!--\s*SYNC_EN_SHA256:\s*([0-9a-f]{64})\s*-->")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_marker(text: str) -> str | None:
    match = MARKER_RE.search(text)
    return match.group(1) if match else None


def build_prompt(readme_text: str) -> str:
    return (
        "Translate the following README from English to Russian.\n"
        "Requirements:\n"
        "1) Preserve markdown structure exactly (headings, lists, code fences, links).\n"
        "2) Keep code, command lines, env var names, and file paths unchanged.\n"
        "3) Keep technical product names in English where appropriate.\n"
        "4) Keep the first language toggle line format with links.\n"
        "5) Return ONLY translated markdown without explanations.\n\n"
        f"{readme_text}"
    )


def request_openai(api_key: str, model: str, prompt: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "You are a precise technical translator."},
            {"role": "user", "content": prompt},
        ],
    }
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"].strip()


def request_anthropic(api_key: str, model: str, prompt: str) -> str:
    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model,
        "max_tokens": 4000,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    parts = body.get("content", [])
    text_parts = [p.get("text", "") for p in parts if p.get("type") == "text"]
    return "\n".join(text_parts).strip()


def translate_readme() -> int:
    load_env_file(ROOT / ".env")
    readme_en = README_EN.read_bytes()
    readme_en_text = readme_en.decode("utf-8")
    digest = sha256_bytes(readme_en)
    provider = os.environ.get("LLM_PROVIDER", "openai").strip().lower()
    model = os.environ.get(
        "LLM_MODEL",
        "gpt-4o-mini" if provider == "openai" else "claude-3-5-sonnet-latest",
    ).strip()
    prompt = build_prompt(readme_en_text)

    try:
        if provider == "openai":
            key = os.environ.get("OPENAI_API_KEY", "").strip()
            if not key:
                print("error: OPENAI_API_KEY is missing. See .env.example.", file=sys.stderr)
                return 2
            translated = request_openai(key, model, prompt)
        elif provider == "anthropic":
            key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
            if not key:
                print("error: ANTHROPIC_API_KEY is missing. See .env.example.", file=sys.stderr)
                return 2
            translated = request_anthropic(key, model, prompt)
        else:
            print(f"error: unsupported LLM_PROVIDER={provider!r}. Use openai or anthropic.", file=sys.stderr)
            return 2
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"error: translation API HTTP {exc.code}: {body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"error: translation API request failed: {exc}", file=sys.stderr)
        return 1

    translated = translated.rstrip() + f"\n\n<!-- SYNC_EN_SHA256: {digest} -->\n"
    README_RU.write_text(translated, encoding="utf-8")
    print(f"updated {README_RU.relative_to(ROOT)} with marker {digest}")
    return 0


def check_sync() -> int:
    if not README_EN.exists():
        print("error: README.md not found", file=sys.stderr)
        return 1
    if not README_RU.exists():
        print("error: README.ru.md not found. Run --translate.", file=sys.stderr)
        return 1
    digest = sha256_bytes(README_EN.read_bytes())
    ru_text = README_RU.read_text(encoding="utf-8")
    found = read_marker(ru_text)
    if found != digest:
        print(
            "README sync check failed: README.md changed.\n"
            "Run: python3 scripts/sync_readme_ru.py --translate",
            file=sys.stderr,
        )
        return 1
    print("README sync check passed.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync README.ru.md with README.md")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--translate", action="store_true", help="Translate README.md into Russian")
    group.add_argument("--check", action="store_true", help="Check README.ru.md marker hash")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.translate:
        return translate_readme()
    return check_sync()


if __name__ == "__main__":
    raise SystemExit(main())
