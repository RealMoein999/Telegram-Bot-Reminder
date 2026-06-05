# Persian ReminderBot – Telegram 

---

This bot helps you remember tasks. Built with Python as a training project.

## What it can do
- Add tasks with `/addtask`
- Set reminders by asking user
- List all pending tasks with `/listtasks`
- Get two reminder messages; one five minutes before and another at the exact time you set
- Mark tasks as done or delete them via buttons
- Ability to track your tasks

## How to run it yourself
1. Clone the repo
2. Install Python 3.8+
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with your bot token (see `.env.example`)
5. Run `python bot.py`

## Deployment
Deployed on Render (free tier) using a webhook to stay online 24/7.

Made by Moein Samadi as a training project.
