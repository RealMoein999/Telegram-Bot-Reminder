import logging
import os
from zoneinfo import ZoneInfo           # <-- built‑in timezone
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    Defaults,
)
import database as db
import handlers

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def main():
    db.init_db()

    # Set default timezone to Iran – all naive datetimes become Asia/Tehran
    app = ApplicationBuilder() \
        .token(TOKEN) \
        .defaults(Defaults(tzinfo=ZoneInfo("Asia/Tehran"))) \
        .build()

    # Conversation handler for /addtask
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addtask", handlers.addtask_start)],
        states={
            handlers.TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.addtask_title)],
            handlers.YEAR: [CallbackQueryHandler(handlers.year_selected, pattern="^year_")],
            handlers.MONTH: [CallbackQueryHandler(handlers.month_selected, pattern="^month_")],
            handlers.DAY: [CallbackQueryHandler(handlers.day_selected, pattern="^day_")],
            handlers.TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.addtask_time),
                CallbackQueryHandler(handlers.go_back_from_time, pattern="^back_to_day$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel_add)],
    )

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("restart", handlers.restart_command))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("showlist", handlers.show_list))

    # Callback handlers
    app.add_handler(CallbackQueryHandler(handlers.show_list, pattern="^toggle_list$"))   # <-- fixed
    app.add_handler(CallbackQueryHandler(handlers.task_done_handler, pattern="^done_"))
    app.add_handler(CallbackQueryHandler(handlers.task_delete_handler, pattern="^del_"))
    app.add_handler(CallbackQueryHandler(handlers.restart_confirm_handler, pattern="^restart_confirm_"))
    # Back navigation callbacks
    app.add_handler(CallbackQueryHandler(handlers.year_selected, pattern="^year_"))
    app.add_handler(CallbackQueryHandler(handlers.month_selected, pattern="^month_"))
    app.add_handler(CallbackQueryHandler(handlers.day_selected, pattern="^day_"))
    app.add_handler(CallbackQueryHandler(handlers.back_to_year, pattern="^back_to_year$"))
    app.add_handler(CallbackQueryHandler(handlers.back_to_month, pattern="^back_to_month$"))
    app.add_handler(CallbackQueryHandler(handlers.back_to_day, pattern="^back_to_day$"))
    app.add_handler(CallbackQueryHandler(handlers.fallback_callback))

    if os.getenv("RENDER"):
        port = int(os.environ.get("PORT", 8443))
        webhook_url = os.environ.get("WEBHOOK_URL")
        print(f"Starting webhook on port {port} with URL {webhook_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
            secret_token="my-secret-token"
        )
    else:
        print("🤖 Bot is running (polling)...")
        app.run_polling()

if __name__ == "__main__":
    main()