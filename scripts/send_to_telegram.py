#!/usr/bin/env python3
"""Send the latest daily AI news briefing to Telegram.

Picks the most recent noticias-ia-YYYY-MM-DD.html file in the repo root,
builds a short Telegram-HTML summary message, and sends it together with
the full HTML file as a document.

Required environment variables:
    TELEGRAM_BOT_TOKEN  Bot token from @BotFather
    TELEGRAM_CHAT_ID    Target chat/channel/group ID

Optional:
    NEWS_FILE           Explicit path to the HTML file to send
                        (overrides auto-detection)
"""

import os
import re
import sys
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
MESSAGE_LIMIT = 4000  # Telegram hard limit is 4096, leave margin


def find_latest_news_file(repo_root: Path) -> Path:
    explicit = os.environ.get("NEWS_FILE")
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"NEWS_FILE not found: {explicit}")
        return path

    pattern = re.compile(r"noticias-ia-(\d{4})-(\d{2})-(\d{2})\.html$")
    candidates = []
    for html in repo_root.glob("noticias-ia-*.html"):
        match = pattern.search(html.name)
        if match:
            candidates.append((date(*map(int, match.groups())), html))

    if not candidates:
        raise FileNotFoundError(
            f"No noticias-ia-YYYY-MM-DD.html file found in {repo_root}"
        )

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def build_summary(html_path: Path) -> str:
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")

    title_tag = soup.find("h1")
    date_tag = soup.find(class_="date")
    title = title_tag.get_text(strip=True) if title_tag else "Daily AI Briefing"
    date_line = date_tag.get_text(strip=True) if date_tag else ""

    lines = [f"<b>{title}</b>"]
    if date_line:
        lines.append(f"<i>{date_line}</i>")
    lines.append("")

    current_section = None
    for element in soup.select(".section-title, .news-item"):
        if "section-title" in element.get("class", []):
            current_section = element.get_text(strip=True)
            lines.append(f"\n<b>— {current_section} —</b>")
            continue

        headline_tag = element.find("h2")
        if not headline_tag:
            continue
        headline = headline_tag.get_text(" ", strip=True)
        source_link = element.select_one(".source a")
        if source_link and source_link.get("href"):
            link = source_link["href"]
            source_name = source_link.get_text(strip=True)
            lines.append(f"• {headline}\n  <a href=\"{link}\">{source_name}</a>")
        else:
            lines.append(f"• {headline}")

    lines.append("\n<i>Archivo HTML completo adjunto ↓</i>")
    message = "\n".join(lines)

    if len(message) > MESSAGE_LIMIT:
        message = message[: MESSAGE_LIMIT - 20].rstrip() + "\n\n… (truncado)"
    return message


def send_message(token: str, chat_id: str, text: str) -> None:
    resp = requests.post(
        TELEGRAM_API.format(token=token, method="sendMessage"),
        data={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        },
        timeout=30,
    )
    resp.raise_for_status()


def send_document(token: str, chat_id: str, html_path: Path) -> None:
    with html_path.open("rb") as f:
        resp = requests.post(
            TELEGRAM_API.format(token=token, method="sendDocument"),
            data={"chat_id": chat_id, "caption": html_path.name},
            files={"document": (html_path.name, f, "text/html")},
            timeout=60,
        )
    resp.raise_for_status()


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set", file=sys.stderr)
        return 1

    repo_root = Path(__file__).resolve().parent.parent
    html_path = find_latest_news_file(repo_root)
    print(f"Sending {html_path.name} to Telegram chat {chat_id}")

    summary = build_summary(html_path)
    send_message(token, chat_id, summary)
    send_document(token, chat_id, html_path)
    print("Sent successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
