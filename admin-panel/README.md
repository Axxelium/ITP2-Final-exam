# Employee Management System (EMS)

Full-Stack admin panel built with Flask, featuring role-based access control
and Telegram notifications.

## Setup

1. Install dependencies:
pip install -r requirements.txt

2. Copy config and fill in your values:
cp config.example.py config.py

3. Seed the database (creates admin and user accounts):
python seed.py

4. Run the app:
python app.py

Open http://127.0.0.1:5000

## Default credentials

| Username | Password  | Role  |
|----------|-----------|-------|
| admin    | admin123  | admin |
| user1    | user123   | user  |

## Telegram bot

- Set `BOT_TOKEN` in `config.py` (get from @BotFather)
- Start the bot in Telegram and send `/start` to subscribe to notifications
- Send `/stop` to unsubscribe
