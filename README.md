# TG Channel Parser

Simple Telegram userbot to export the latest N posts from specified channels into a CSV.

## Requirements

- Python 3.9+
- Telegram API credentials

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Get your Telegram API credentials at [my.telegram.org](https://my.telegram.org/auth?to=apps).

3. Set environment variables:

```bash
export TG_API_ID=123456
export TG_API_HASH=your_api_hash
```

Or create a `.env` file (see `.env.example`) and keep variables there.

4. Edit `config.txt`:

```
channels=@example_channel1,@example_channel2
limit=50
output=out.csv
login_mode=qr
```

## Run

```bash
python main.py
```

On first run, Telethon will ask for your phone number and login code.
For QR login, set `login_mode=qr` (or env `LOGIN_MODE=qr`) and scan the QR code shown in the terminal.

## Output

CSV with columns: `channel`, `message_id`, `date`, `text`.
Text is converted to Markdown-like format and preserves line breaks.
