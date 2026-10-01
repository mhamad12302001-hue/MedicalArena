import os
import sqlite3

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from contextlib import asynccontextmanager


# =========================
# إعدادات البوت
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================
# قاعدة البيانات
# =========================

DB_NAME = "medical_arena.db"


def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            rating INTEGER DEFAULT 1000,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def create_user(message: Message):
    user = message.from_user

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, first_name)
        VALUES (?, ?, ?)
    """, (
        user.id,
        user.username,
        user.first_name
    ))

    cursor.execute("""
        UPDATE users
        SET username = ?, first_name = ?
        WHERE user_id = ?
    """, (
        user.username,
        user.first_name,
        user.id
    ))

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, username, first_name,
               xp, level, rating, wins, losses
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    user = cursor.fetchone()

    conn.close()

    return user


# =========================
# لوحة المفاتيح الرئيسية
# =========================

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎯 ابدأ اللعب"),
            KeyboardButton(text="📚 التدريب"),
        ],
        [
            KeyboardButton(text="🏆 المتصدرون"),
            KeyboardButton(text="👤 ملفي"),
        ],
        [
            KeyboardButton(text="🎖️ الإنجازات"),
            KeyboardButton(text="📊 إحصائياتي"),
        ],
        [
            KeyboardButton(text="⚙️ الإعدادات"),
            KeyboardButton(text="❓ المساعدة"),
        ],
    ],
    resize_keyboard=True
)


# =========================
# /start
# =========================

@dp.message(CommandStart())
async def start_command(message: Message):
    create_user(message)

    text = (
        "🩺 <b>مرحباً بك في الساحة الطبية</b>\n\n"
        "هنا تستطيع اختبار معلوماتك الطبية، "
        "التدرب وتطوير مستواك.\n\n"
        "👤 تم إنشاء حسابك بنجاح.\n\n"
        "اختر ما تريد القيام به:"
    )

    await message.answer(
        text,
        reply_markup=main_keyboard,
        parse_mode="HTML"
    )


# =========================
# ابدأ اللعب
# =========================

@dp.message(F.text == "🎯 ابدأ اللعب")
async def start_game(message: Message):
    await message.answer(
        "🎯 <b>ابدأ اللعب</b>\n\n"
        "سيتم إضافة نظام المباريات والأسئلة التنافسية هنا قريباً.\n\n"
        "⚔️ 1 ضد 1\n"
        "🎲 مباراة عشوائية\n"
        "👥 تحدي صديق",
        parse_mode="HTML"
    )


# =========================
# التدريب
# =========================

@dp.message(F.text == "📚 التدريب")
async def training(message: Message):
    await message.answer(
        "📚 <b>وضع التدريب</b>\n\n"
        "قسم التدريب جاهز للتطوير.\n\n"
        "سيتم إضافة الأسئلة والتخصصات "
        "ومستويات الصعوبة في الخطوة القادمة.",
        parse_mode="HTML"
    )


# =========================
# ملفي
# =========================

@dp.message(F.text == "👤 ملفي")
async def profile(message: Message):
    create_user(message)

    user = get_user(message.from_user.id)

    if not user:
        await message.answer("حدث خطأ في تحميل الملف الشخصي.")
        return

    _, username, first_name, xp, level, rating, wins, losses = user

    username_text = f"@{username}" if username else "غير محدد"

    text = (
        "👤 <b>ملفك الشخصي</b>\n\n"
        f"🧑 الاسم: {first_name}\n"
        f"🔹 Username: {username_text}\n\n"
        f"⭐ XP: {xp}\n"
        f"🎚️ المستوى: {level}\n"
        f"🏆 التقييم: {rating}\n"
        f"✅ الانتصارات: {wins}\n"
        f"❌ الخسارات: {losses}"
    )

    await message.answer(
        text,
        parse_mode="HTML"
    )


# =========================
# المتصدرون
# =========================

@dp.message(F.text == "🏆 المتصدرون")
async def leaderboard(message: Message):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT first_name, username, rating, level
        FROM users
        ORDER BY rating DESC
        LIMIT 10
    """)

    users = cursor.fetchall()

    conn.close()

    if not users:
        await message.answer(
            "🏆 لا يوجد لاعبون حتى الآن."
        )
        return

    text = "🏆 <b>المتصدرون</b>\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for index, user in enumerate(users, start=1):
        first_name, username, rating, level = user

        medal = medals[index - 1] if index <= 3 else f"{index}."

        text += (
            f"{medal} {first_name} — "
            f"⭐ {rating} | المستوى {level}\n"
        )

    await message.answer(
        text,
        parse_mode="HTML"
    )


# =========================
# الإنجازات
# =========================

@dp.message(F.text == "🎖️ الإنجازات")
async def achievements(message: Message):
    await message.answer(
        "🎖️ <b>الإنجازات</b>\n\n"
        "🔒 لم يتم فتح نظام الإنجازات بعد.\n\n"
        "سيتم إضافة الإنجازات مثل:\n"
        "🏅 أول انتصار\n"
        "🔥 سلسلة انتصارات\n"
        "🧠 100 سؤال صحيح\n"
        "🏆 الوصول إلى مستوى متقدم",
        parse_mode="HTML"
    )


# =========================
# الإحصائيات
# =========================

@dp.message(F.text == "📊 إحصائياتي")
async def statistics(message: Message):
    user = get_user(message.from_user.id)

    if not user:
        create_user(message)
        user = get_user(message.from_user.id)

    _, _, _, xp, level, rating, wins, losses = user

    total_games = wins + losses

    if total_games > 0:
        win_rate = round((wins / total_games) * 100, 1)
    else:
        win_rate = 0

    text = (
        "📊 <b>إحصائياتك</b>\n\n"
        f"⭐ XP: {xp}\n"
        f"🎚️ المستوى: {level}\n"
        f"🏆 التقييم: {rating}\n"
        f"🎮 مجموع المباريات: {total_games}\n"
        f"✅ الانتصارات: {wins}\n"
        f"❌ الخسارات: {losses}\n"
        f"📈 نسبة الفوز: {win_rate}%"
    )

    await message.answer(
        text,
        parse_mode="HTML"
    )


# =========================
# الإعدادات
# =========================

@dp.message(F.text == "⚙️ الإعدادات")
async def settings(message: Message):
    await message.answer(
        "⚙️ <b>الإعدادات</b>\n\n"
        "سيتم إضافة إعدادات اللغة والإشعارات "
        "والخصوصية هنا لاحقاً.",
        parse_mode="HTML"
    )


# =========================
# المساعدة
# =========================

@dp.message(F.text == "❓ المساعدة")
async def help_command(message: Message):
    await message.answer(
        "❓ <b>مساعدة Medical Arena</b>\n\n"
        "🩺 الساحة الطبية هي منصة تعليمية تنافسية "
        "لاختبار وتطوير المعلومات الطبية.\n\n"
        "📚 التدريب — للتعلم وحل الأسئلة\n"
        "🎯 اللعب — للمنافسة\n"
        "👤 ملفي — معلوماتك ومستواك\n"
        "🏆 المتصدرون — ترتيب اللاعبين\n"
        "📊 إحصائياتي — إحصائياتك",
        parse_mode="HTML"
    )


# =========================
# رسائل غير معروفة
# =========================

@dp.message()
async def unknown_message(message: Message):
    await message.answer(
        "🩺 اختر أحد الخيارات من القائمة الرئيسية.",
        reply_markup=main_keyboard
    )


# =========================
# FastAPI + Telegram Webhook
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):

    init_database()

    if WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL + WEBHOOK_PATH
        )

    yield

    await bot.delete_webhook()
    await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def home():
    return {
        "status": "Medical Arena is running"
    }


@app.get("/health")
async def health():
    return {
        "status": "ok"
    }


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):

    data = await request.json()

    await dp.feed_raw_update(
        bot,
        data
    )

    return {
        "ok": True
    }