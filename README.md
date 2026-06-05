# RemindMeBot – Telegram 

---

This bot helps you remember tasks. Built with Python as a learning project.

## What it can do
- Add tasks with `/addtask`
- Set reminders like `/addtask Buy milk ; 2026-12-24 18:00`
- List all pending tasks with `/listtasks`
- Get a reminder message at the exact time you set
- Mark tasks as done or delete them via buttons

## How to run it yourself
1. Clone the repo
2. Install Python 3.8+
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with your bot token (see `.env.example`)
5. Run `python bot.py`

## Deployment
Deployed on Render (free tier) using a webhook to stay online 24/7.

Made with ❤️ and lots of curiosity.