import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo                    # <-- built‑in
import jdatetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import database as db

logger = logging.getLogger(__name__)

TITLE, YEAR, MONTH, DAY, TIME = range(5)

def persian_month_name(month_number: int) -> str:
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    return months[month_number - 1] if 1 <= month_number <= 12 else ""

# ---------- Keyboards ----------
def year_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1405", callback_data="year_1405"),
         InlineKeyboardButton("1406", callback_data="year_1406"),
         InlineKeyboardButton("1407", callback_data="year_1407")]
    ])

def month_keyboard():
    months = [
        ("فروردین",1),("اردیبهشت",2),("خرداد",3),("تیر",4),
        ("مرداد",5),("شهریور",6),("مهر",7),("آبان",8),
        ("آذر",9),("دی",10),("بهمن",11),("اسفند",12)
    ]
    keyboard = []
    row = []
    for name, num in months:
        row.append(InlineKeyboardButton(name, callback_data=f"month_{num}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_year")])
    return InlineKeyboardMarkup(keyboard)

def day_keyboard(year, month):
    try:
        test_date = jdatetime.date(year, month, 1)
        if month == 12:
            next_month = jdatetime.date(year + 1, 1, 1)
        else:
            next_month = jdatetime.date(year, month + 1, 1)
        max_days = (next_month - test_date).days
    except:
        max_days = 30
    buttons = []
    row = []
    for d in range(1, max_days + 1):
        row.append(InlineKeyboardButton(str(d), callback_data=f"day_{d}"))
        if len(row) == 7:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_month")])
    return InlineKeyboardMarkup(buttons)

def time_inline_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_day")]
    ])
# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name
    await update.message.reply_text(
        f"سلام «{name}»🖐 به ربات یادآور خوش اومدی\n\n"
        "این ربات چیکار میتونه بکنه؟\n"
        "این ربات با دریافت فعالیت، تاریخ و ساعت رویداد، "
        "۵ دقیقه قبل از شروع رویداد و در لحظه شروع به شما اطلاع میده.\n\n"
        "📌 از منوی پایین یا دستورات زیر استفاده کن:\n"
        "/addtask – افزودن رویداد\n"
        "/showlist – لیست رویدادها\n"
        "/restart – شروع مجدد"
    )

# ---------- RESTART ----------
async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✅ بله، حذف همه", callback_data="restart_confirm_yes"),
         InlineKeyboardButton("❌ خیر", callback_data="restart_confirm_no")]
    ]
    await update.message.reply_text(
        "⚠️ آیا مطمئنی که می‌خواهی همه رویدادهایت حذف شود؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def restart_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data.split("_")[-1]
    if choice == "yes":
        user_id = update.effective_user.id
        db.delete_all_tasks(user_id)
        context.user_data.clear()
        await query.edit_message_text("✅ همه رویدادها حذف شدند. ربات دوباره راه‌اندازی شد.")
        await start(update, context)
    else:
        await query.edit_message_text("❌ عملیات لغو شد.")

# ---------- /addtask conversation ----------
async def addtask_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 عنوان رویداد را وارد کنید:")
    return TITLE

async def addtask_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_title"] = update.message.text.strip()
    await update.message.reply_text(
        "📅 سال رویداد را انتخاب کنید (شمسی):",
        reply_markup=year_keyboard()
    )
    return YEAR

# Back navigation
async def back_to_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📅 سال رویداد را انتخاب کنید (شمسی):",
        reply_markup=year_keyboard()
    )
    return YEAR

async def year_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    year = int(query.data.split("_")[1])
    context.user_data["year"] = year
    await query.edit_message_text(
        f"سال {year} انتخاب شد.\nحالا ماه را انتخاب کنید:",
        reply_markup=month_keyboard()
    )
    return MONTH

async def month_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    month = int(query.data.split("_")[1])
    context.user_data["month"] = month
    year = context.user_data["year"]
    month_name = persian_month_name(month)
    await query.edit_message_text(
        f"سال {year}، ماه {month_name}\nحالا روز را انتخاب کنید:",
        reply_markup=day_keyboard(year, month)
    )
    return DAY

async def day_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = int(query.data.split("_")[1])
    context.user_data["day"] = day
    year = context.user_data["year"]
    month = context.user_data["month"]
    month_name = persian_month_name(month)
    await query.edit_message_text(
        f"تاریخ انتخاب شده: {day} {month_name} {year}\n\n"
        "⏰ حالا ساعت دقیق به ۲۴ ساعت وارد کنید (HH:MM):",
        reply_markup=time_inline_keyboard()          # ✅ now an inline keyboard
    )
    return TIME


async def go_back_from_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback when back button is pressed in time state."""
    query = update.callback_query
    await query.answer()
    year = context.user_data.get("year", 1405)
    month = context.user_data.get("month", 1)
    await query.edit_message_text(
        f"سال {year}، ماه {persian_month_name(month)}\nحالا روز را انتخاب کنید:",
        reply_markup=day_keyboard(year, month)
    )
    return DAY


async def back_to_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    year = context.user_data.get("year", 1405)
    await query.edit_message_text(
        f"سال {year} انتخاب شد.\nحالا ماه را انتخاب کنید:",
        reply_markup=month_keyboard()
    )
    return MONTH

async def back_to_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    year = context.user_data.get("year", 1405)
    month = context.user_data.get("month", 1)
    await query.edit_message_text(
        f"سال {year}، ماه {persian_month_name(month)}\nحالا روز را انتخاب کنید:",
        reply_markup=day_keyboard(year, month)
    )
    return DAY

async def addtask_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    time_str = update.message.text.strip()
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await update.message.reply_text("❌ قالب ساعت اشتباه است. لطفاً به صورت HH:MM وارد کنید:")
        return TIME

    user_id = update.effective_user.id
    title = context.user_data["task_title"]
    year = context.user_data["year"]
    month = context.user_data["month"]
    day = context.user_data["day"]
    hour, minute = map(int, time_str.split(":"))

    try:
        jdt = jdatetime.datetime(year, month, day, hour, minute)
        deadline = jdt.togregorian()   # naive datetime, bot default = Asia/Tehran
    except Exception:
        await update.message.reply_text("❌ تاریخ/ساعت نامعتبر است. فرآیند لغو شد.")
        context.user_data.clear()
        return ConversationHandler.END

    now_tehran = datetime.now(ZoneInfo("Asia/Tehran")).replace(tzinfo=None)
    if deadline <= now_tehran:
        await update.message.reply_text("⚠️ زمان انتخاب شده گذشته است. رویداد ثبت نشد.")
        context.user_data.clear()
        return ConversationHandler.END

    remind_at_str = deadline.strftime("%Y-%m-%d %H:%M")
    task_id = db.add_task(user_id, title, remind_at_str)

    warn_time = deadline - timedelta(minutes=5)
    if warn_time > now_tehran:
        context.job_queue.run_once(
            send_5min_warning,
            when=warn_time,
            chat_id=update.effective_chat.id,
            data={"task_id": task_id, "task_text": title},
            name=f"warn_{task_id}"
        )
    context.job_queue.run_once(
        deadline_alert,
        when=deadline,
        chat_id=update.effective_chat.id,
        data={"task_id": task_id, "task_text": title, "user_id": user_id},
        name=f"dead_{task_id}"
    )

    j_deadline = jdatetime.datetime.fromgregorian(datetime=deadline)
    persian_date_str = f"{j_deadline.day} {persian_month_name(j_deadline.month)} {j_deadline.year}"
    await update.message.reply_text(
        f"✅ رویداد «{title}»\n"
        f"📅 تاریخ: {persian_date_str}\n"
        f"⏰ ساعت: {j_deadline.hour:02d}:{j_deadline.minute:02d}\n"
        f"ثبت شد!",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# ---------- Reminders ----------
async def send_5min_warning(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"⏳ به رویداد «{job.data['task_text']}» کمتر از ۵ دقیقه باقی مانده!"
    )

async def deadline_alert(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    db.mark_done(job.data["task_id"], job.data["user_id"])
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"⏰ ددلاین رویداد «{job.data['task_text']}» رسید."
    )

# ---------- /showlist ----------
async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This function handles both the /showlist command and the toggle button.
    user_id = update.effective_user.id
    if update.callback_query:
        await update.callback_query.answer()
        # Toggle the show_done flag
        context.user_data["show_done"] = not context.user_data.get("show_done", False)
        message = update.callback_query.message
    else:
        context.user_data["show_done"] = False
        message = update.message

    pending = db.get_tasks(user_id, only_pending=True)
    done = db.get_tasks(user_id, only_pending=False)
    done = [t for t in done if t[3] == 1]

    # Pending tasks with action buttons
    if pending:
        pending.sort(key=lambda t: t[2] if t[2] else "9999")
        now_tehran = datetime.now(ZoneInfo("Asia/Tehran")).replace(tzinfo=None)
        lines = []
        for task_id, task_text, remind_at_str, is_done in pending:
            try:
                greg_dt = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M")
                jdt = jdatetime.datetime.fromgregorian(datetime=greg_dt)
                persian_date = f"{jdt.day} {persian_month_name(jdt.month)} {jdt.year}"
                persian_time = f"{jdt.hour:02d}:{jdt.minute:02d}"
                display_time = f"{persian_date} ساعت {persian_time}"
            except:
                display_time = remind_at_str
            remaining = greg_dt - now_tehran
            total_sec = remaining.total_seconds()
            if total_sec <= 0:
                color = "🟥"; rem_text = "0 ثانیه"
            elif total_sec > 3600:
                color = "🟦"
                h = int(total_sec // 3600)
                m = int((total_sec % 3600) // 60)
                rem_text = f"{h} ساعت و {m} دقیقه"
            elif total_sec > 60:
                color = "🟨"
                m = int(total_sec // 60)
                s = int(total_sec % 60)
                rem_text = f"{m} دقیقه و {s} ثانیه"
            else:
                color = "🟥"
                s = int(total_sec)
                rem_text = f"{s} ثانیه"
            lines.append(f"{color} ⏳ {task_text}\n   ⏱ {rem_text} مانده | 📅 {display_time}")

        task_list_text = "\n\n".join(lines)
        keyboard = []
        for tid, _, _, _ in pending:
            keyboard.append([
                InlineKeyboardButton("✅ انجام", callback_data=f"done_{tid}"),
                InlineKeyboardButton("🗑️ حذف", callback_data=f"del_{tid}")
            ])
        keyboard.append([InlineKeyboardButton(
            "🔁 نمایش انجام‌شده‌ها" if not context.user_data.get("show_done", False) else "🔁 نمایش فقط جاری",
            callback_data="toggle_list"
        )])
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "📋 **رویدادهای در انتظار:**\n" + task_list_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await message.reply_text(
                "📋 **رویدادهای در انتظار:**\n" + task_list_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    else:
        no_pending_text = "📭 هیچ رویداد در انتظاری وجود ندارد."
        if update.callback_query:
            await update.callback_query.edit_message_text(no_pending_text)
        else:
            await message.reply_text(no_pending_text)

    # Done tasks (read-only, sent separately)
    if done and context.user_data.get("show_done", False):
        done.sort(key=lambda t: t[2] if t[2] else "9999", reverse=True)
        lines = []
        for _, task_text, remind_at_str, _ in done:
            try:
                greg_dt = datetime.strptime(remind_at_str, "%Y-%m-%d %H:%M")
                jdt = jdatetime.datetime.fromgregorian(datetime=greg_dt)
                persian_date = f"{jdt.day} {persian_month_name(jdt.month)} {jdt.year}"
                persian_time = f"{jdt.hour:02d}:{jdt.minute:02d}"
                display_time = f"{persian_date} ساعت {persian_time}"
            except:
                display_time = remind_at_str
            lines.append(f"✅ {task_text} — {display_time}")
        if update.callback_query:
            await update.callback_query.message.reply_text(
                "📜 **رویدادهای انجام شده:**\n" + "\n".join(lines),
                parse_mode="Markdown"
            )
        else:
            await message.reply_text(
                "📜 **رویدادهای انجام شده:**\n" + "\n".join(lines),
                parse_mode="Markdown"
            )

# ---------- Task action callbacks ----------
async def task_done_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[1])
    user_id = update.effective_user.id
    if db.mark_done(task_id, user_id):
        current_jobs = context.job_queue.jobs()
        for job in current_jobs:
            if job.name and str(task_id) in job.name:
                job.schedule_removal()
        await query.edit_message_text("✅ رویداد به عنوان انجام شده علامت خورد.")
    else:
        await query.edit_message_text("❌ خطا در به‌روزرسانی.")

async def task_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split("_")[1])
    user_id = update.effective_user.id
    if db.delete_task(task_id, user_id):
        current_jobs = context.job_queue.jobs()
        for job in current_jobs:
            if job.name and str(task_id) in job.name:
                job.schedule_removal()
        await query.edit_message_text("🗑️ رویداد حذف شد.")
    else:
        await query.edit_message_text("❌ خطا در حذف.")

# ---------- Fallback ----------
async def fallback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("این دکمه غیرفعال است.")