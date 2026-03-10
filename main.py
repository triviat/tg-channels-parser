import csv
import os
import sys
from datetime import datetime
from typing import Dict, List

from telethon import TelegramClient
from telethon.extensions import markdown
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
import qrcode


CONFIG_PATH = "config.txt"
SESSION_NAME = "user"


def parse_config(path: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or line.startswith(";"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                cleaned = value.strip()
                if "#" in cleaned:
                    cleaned = cleaned.split("#", 1)[0].strip()
                if ";" in cleaned:
                    cleaned = cleaned.split(";", 1)[0].strip()
                data[key.strip()] = cleaned
    except FileNotFoundError:
        print(f"Config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    return data


def parse_channels(raw: str) -> List[str]:
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",")]
    channels = [p for p in parts if p]
    return channels


def get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"Missing environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def to_markdown_text(message_text: str, entities) -> str:
    if not message_text:
        return ""
    try:
        return markdown.unparse(message_text, entities or [])
    except Exception:
        # Fallback to raw text if entities parsing fails.
        return message_text


def print_qr(url: str) -> None:
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


def main() -> None:
    load_dotenv()
    config = parse_config(CONFIG_PATH)
    channels = parse_channels(config.get("channels", ""))
    if not channels:
        print("No channels configured in config.txt (key: channels).", file=sys.stderr)
        sys.exit(1)

    limit_raw = config.get("limit", "50")
    try:
        limit = int(limit_raw)
    except ValueError:
        print(f"Invalid limit: {limit_raw}", file=sys.stderr)
        sys.exit(1)

    output_path = config.get("output", "out.csv")
    login_mode = os.getenv("LOGIN_MODE", config.get("login_mode", "code")).strip().lower()

    api_id = int(get_env("TG_API_ID"))
    api_hash = get_env("TG_API_HASH")

    client = TelegramClient(SESSION_NAME, api_id, api_hash)

    rows: List[List[str]] = []

    async def fetch() -> None:
        await client.connect()
        try:
            if login_mode == "qr":
                if not await client.is_user_authorized():
                    print("Login mode: qr")
                    try:
                        qr_login = await client.qr_login()
                    except AttributeError:
                        print("QR login is not supported by your Telethon version. Update dependencies.", file=sys.stderr)
                        sys.exit(1)
                    print("Scan this QR code in Telegram (Settings -> Devices -> Scan QR):")
                    print_qr(qr_login.url)
                    try:
                        await qr_login.wait()
                    except SessionPasswordNeededError:
                        password = input("Two-step verification enabled. Enter your password: ")
                        await client.sign_in(password=password)
            else:
                await client.start()

            for channel in channels:
                messages = []
                async for msg in client.iter_messages(channel, limit=limit):
                    messages.append(msg)
                # iter_messages returns newest first; reverse to oldest -> newest
                for msg in reversed(messages):
                    text = to_markdown_text(msg.message or "", msg.entities)
                    date_str = ""
                    if isinstance(msg.date, datetime):
                        date_str = msg.date.isoformat()
                    rows.append([channel, str(msg.id), date_str, text])
        finally:
            await client.disconnect()

    client.loop.run_until_complete(fetch())

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(["channel", "message_id", "date", "text"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} messages to {output_path}")


if __name__ == "__main__":
    main()
