from __future__ import annotations

from parser import parse_email


def test_parse_email_prefers_text_plain() -> None:
    raw = (
        b"From: sender@example.com\r\n"
        b"Subject: Test\r\n"
        b"Date: Fri, 17 Apr 2026 12:00:00 +0000\r\n"
        b"Message-ID: <abc@example.com>\r\n"
        b"MIME-Version: 1.0\r\n"
        b"Content-Type: multipart/alternative; boundary=sep\r\n"
        b"\r\n"
        b"--sep\r\n"
        b"Content-Type: text/plain; charset=utf-8\r\n"
        b"\r\n"
        b"plain body\r\n"
        b"--sep\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"\r\n"
        b"<html><body><p>html body</p></body></html>\r\n"
        b"--sep--\r\n"
    )
    parsed = parse_email(raw)
    assert parsed["body"] == "plain body"
    assert parsed["dedup_key"] == "mid:abc@example.com"


def test_parse_email_falls_back_to_html() -> None:
    raw = (
        b"From: sender@example.com\r\n"
        b"Subject: Html only\r\n"
        b"Date: Fri, 17 Apr 2026 12:00:00 +0000\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"\r\n"
        b"<html><body><h1>Hello</h1><p>Line<br>Two</p></body></html>\r\n"
    )
    parsed = parse_email(raw)
    assert "Hello" in parsed["body"]
    assert "Line" in parsed["body"]
    assert "Two" in parsed["body"]
