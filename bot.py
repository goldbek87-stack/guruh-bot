# -*- coding: utf-8 -*-
"""
Ob'ektivka (МАЪЛУМОТНОМА) tayyorlovchi Telegram bot.

Ishga tushirish:  python bot.py
(oldin .env faylga BOT_TOKEN ni yozing, requirements.txt ni o'rnating,
 tizimda ffmpeg bo'lishi shart)
"""
import os
import logging
import uuid
import asyncio

from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton
from telegram.ext import (
    Application, ContextTypes, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters,
)

from config import BOT_TOKEN, TMP_DIR, WEBHOOK_HOST, PORT
from transcribe import transcribe_ogg
from doc_builder import build_document
import texts as T

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ============================== YORDAMCHI ==================================

def kb(*rows):
    """rows: [[(text, callback_data), ...], ...]"""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text, callback_data=cb) for text, cb in row] for row in rows]
    )


def reset_user(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["data"] = {}
    context.user_data["mehnat"] = []
    context.user_data["relatives"] = []
    context.user_data["step_idx"] = 0
    context.user_data["phase"] = "lang"
    context.user_data["awaiting"] = None
    context.user_data["has_spouse"] = False
    context.user_data["family_shared_address"] = None
    context.user_data["spouse_shared_address"] = None


def lang_of(context) -> str:
    return context.user_data.get("lang", T.L)


_LOWERCASE_SUFFIXES = {"o'g'li", "o’g’li", "qizi", "ўғли", "қизи"}


def smart_capitalize_name(text: str) -> str:
    """Ism-familiya kabi maydonlarda har bir so'zning birinchi harfini
    katta qiladi, "o'g'li"/"qizi" kabi qo'shimchalarni kichik holicha qoldiradi."""
    words = text.strip().split()
    out = []
    for w in words:
        if w.lower() in _LOWERCASE_SUFFIXES:
            out.append(w.lower())
        elif w:
            out.append(w[0].upper() + w[1:])
        else:
            out.append(w)
    return " ".join(out)


_FAMILY_GROUP_KEYS = {"ota", "ona", "aka", "uka", "opa", "singil"}
_SPOUSE_GROUP_KEYS = {"spouse", "farzand"}


def shared_address_for(rel_key: str, context: ContextTypes.DEFAULT_TYPE):
    if rel_key in _FAMILY_GROUP_KEYS:
        return context.user_data.get("family_shared_address")
    if rel_key in _SPOUSE_GROUP_KEYS:
        return context.user_data.get("spouse_shared_address")
    return None


# ============================== START / LANG ================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_user(context)
    await update.message.reply_text(
        T.START_PROMPT,
        reply_markup=kb([("🇺🇿 Lotin", "lang_lat"), ("Кирилл", "lang_cyr")]),
    )


async def on_lang_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = T.L if query.data == "lang_lat" else T.C
    context.user_data["lang"] = lang
    context.user_data["phase"] = "simple"
    context.user_data["step_idx"] = 0
    await ask_current_simple_step(query, context)


# ============================== ODDIY MAYDONLAR ==============================

async def ask_current_simple_step(target, context: ContextTypes.DEFAULT_TYPE):
    lang = lang_of(context)
    idx = context.user_data["step_idx"]
    steps = T.SIMPLE_STEPS
    if idx >= len(steps):
        # oddiy maydonlar tugadi -> mehnat fazasiga o'tamiz
        context.user_data["phase"] = "mehnat"
        await start_mehnat(target, context)
        return

    step = steps[idx]
    prompt = step["prompt"][0] if lang == T.L else step["prompt"][1]
    text = f"{idx + 1}/{len(steps)}. {prompt}{T.ASK_VOICE_HINT[lang]}"

    reply_markup = None
    if step.get("quick_no"):
        reply_markup = kb([(T.BTN_QUICK_NO[lang], "quickno")])

    await target.message.reply_text(text, reply_markup=reply_markup)


async def on_quick_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = lang_of(context)
    if context.user_data.get("phase") != "simple":
        return
    idx = context.user_data["step_idx"]
    key = T.SIMPLE_STEPS[idx]["key"]
    context.user_data["data"][key] = T.QUICK_NO_TEXT[lang]
    context.user_data["step_idx"] += 1
    await ask_current_simple_step(query, context)


# ============================== OVOZ / MATN QABUL QILISH ====================

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = lang_of(context)
    phase = context.user_data.get("phase")
    if phase is None:
        await update.message.reply_text(T.NOT_STARTED_MSG[lang])
        return
    if phase in ("lang", "photo", "done"):
        return

    voice = update.message.voice or update.message.audio
    if voice is None:
        return

    tg_file = await context.bot.get_file(voice.file_id)
    ogg_path = os.path.join(TMP_DIR, f"{uuid.uuid4().hex}.ogg")
    await tg_file.download_to_drive(ogg_path)

    waiting = await update.message.reply_text(
        "⏳" if lang == T.L else "⏳"
    )
    text = transcribe_ogg(ogg_path)
    try:
        await waiting.delete()
    except Exception:
        pass

    if not text:
        await update.message.reply_text(T.TRANSCRIBE_FAIL[lang])
        return

    context.user_data["pending_text"] = text
    await update.message.reply_text(
        T.CONFIRM_PREVIEW[lang].format(text=text),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(T.BTN_CONFIRM[lang], callback_data="confirm")],
            [InlineKeyboardButton(T.BTN_COPY[lang], copy_text=CopyTextButton(text=text))],
        ]),
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phase = context.user_data.get("phase")
    lang = lang_of(context)
    if phase is None:
        await update.message.reply_text(T.NOT_STARTED_MSG[lang])
        return
    if phase in ("lang", "photo", "done"):
        return

    text = update.message.text.strip()
    if not text:
        return

    # Matn har doim to'g'ridan-to'g'ri javob sifatida qabul qilinadi
    # (foydalanuvchi o'zi yozgani uchun tasdiqlash shart emas)
    context.user_data.pop("pending_text", None)
    await save_answer_and_advance(update, context, text)


async def on_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = context.user_data.pop("pending_text", None)
    if text is None:
        return
    await save_answer_and_advance(query, context, text)


async def on_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = lang_of(context)
    await query.message.reply_text(T.EDIT_ASK_TEXT[lang])
    # keyingi matn xabari to'g'ridan-to'g'ri handle_text orqali qabul qilinadi


# ============================== MARKAZIY DISPATCH ============================

async def save_answer_and_advance(target, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    target: Update (matn holatida) yoki CallbackQuery (tasdiqlash holatida) —
    ikkalasida ham .message orqali javob yozish mumkin.
    """
    awaiting = context.user_data.get("awaiting")
    if awaiting == "family_address":
        context.user_data["family_shared_address"] = text
        context.user_data["awaiting"] = None
        await start_relative_category(target, context)
        return
    if awaiting == "spouse_address":
        context.user_data["spouse_shared_address"] = text
        context.user_data["awaiting"] = None
        await begin_relative_entry(target, context)
        return

    phase = context.user_data.get("phase")

    if phase == "simple":
        idx = context.user_data["step_idx"]
        key = T.SIMPLE_STEPS[idx]["key"]
        if key == "fio":
            text = smart_capitalize_name(text)
        context.user_data["data"][key] = text
        context.user_data["step_idx"] += 1
        await ask_current_simple_step(target, context)

    elif phase == "mehnat":
        await mehnat_save_field(target, context, text)

    elif phase == "relative":
        await relative_save_field(target, context, text)

    else:
        pass


# ============================== MEHNAT FAOLIYATI =============================

async def start_mehnat(target, context: ContextTypes.DEFAULT_TYPE):
    lang = lang_of(context)
    context.user_data["mehnat_sub"] = 0
    context.user_data.setdefault("current_mehnat", {})
    await target.message.reply_text(T.MEHNAT_INTRO[lang])
    await ask_mehnat_field(target, context)


async def ask_mehnat_field(target, context: ContextTypes.DEFAULT_TYPE):
    lang = lang_of(context)
    sub = context.user_data["mehnat_sub"]
    prompts = [T.MEHNAT_FROM_PROMPT, T.MEHNAT_TO_PROMPT, T.MEHNAT_PLACE_PROMPT]
    text = prompts[sub][lang] + T.ASK_VOICE_HINT[lang]
    await target.message.reply_text(text)


async def mehnat_save_field(target, context: ContextTypes.DEFAULT_TYPE, text: str):
    lang = lang_of(context)
    sub = context.user_data["mehnat_sub"]
    cur = context.user_data["current_mehnat"]
    field_names = ["from", "to", "place"]
    cur[field_names[sub]] = text
    sub += 1
    if sub < 3:
        context.user_data["mehnat_sub"] = sub
        await ask_mehnat_field(target, context)
    else:
        context.user_data["mehnat"].append(cur)
        context.user_data["current_mehnat"] = {}
        context.user_data["mehnat_sub"] = 0
        await target.message.reply_text(
            T.MEHNAT_ADD_MORE_PROMPT[lang],
            reply_markup=kb([(T.BTN_ADD_MORE[lang], "mehnat_more_yes"),
                              (T.BTN_NO_MORE[lang], "mehnat_more_no")]),
        )


async def on_mehnat_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "mehnat_more_yes":
        await ask_mehnat_field(query, context)
    else:
        context.user_data["phase"] = "relative"
        context.user_data["rel_cat_idx"] = 0
        context.user_data["relatives"] = context.user_data.get("relatives", [])
        lang = lang_of(context)
        await query.message.reply_text(T.RELATIVES_INTRO[lang])
        await ask_family_gate(query, context)


async def ask_family_gate(target, context: ContextTypes.DEFAULT_TYPE):
    lang = lang_of(context)
    await target.message.reply_text(
        T.FAMILY_GATE_PROMPT[lang],
        reply_markup=kb([(T.BTN_YES[lang], "famgate_yes"), (T.BTN_NO[lang], "famgate_no")]),
    )


async def on_family_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = lang_of(context)
    if query.data == "famgate_yes":
        context.user_data["awaiting"] = "family_address"
        text = T.SHARED_ADDRESS_ASK[lang] + T.ASK_VOICE_HINT[lang]
        await query.message.reply_text(text)
    else:
        context.user_data["family_shared_address"] = None
        await start_relative_category(query, context)


# ============================== QARINDOSHLAR =================================

def _current_spec(context):
    idx = context.user_data["rel_cat_idx"]
    plan = T.RELATIVE_PLAN
    if idx >= len(plan):
        return None
    return plan[idx]


async def start_relative_category(target, context: ContextTypes.DEFAULT_TYPE):
    lang = lang_of(context)
    spec = _current_spec(context)

    if spec is None:
        context.user_data["phase"] = "photo"
        await target.message.reply_text(T.PHOTO_PROMPT[lang])
        return

    if spec.get("requires_spouse") and not context.user_data.get("has_spouse"):
        context.user_data["rel_cat_idx"] += 1
        await start_relative_category(target, context)
        return

    label = spec["label"][0] if lang == T.L else spec["label"][1]

    if spec.get("gated"):
        text = T.PRESENCE_PROMPT[lang].format(label=label)
        await target.message.reply_text(
            text,
            reply_markup=kb([(T.BTN_YES[lang], "presence_yes"), (T.BTN_NO[lang], "presence_no")]),
        )
    else:
        await begin_relative_entry(target, context)


async def begin_relative_entry(target, context: ContextTypes.DEFAULT_TYPE):
    lang = lang_of(context)
    spec = _current_spec(context)
    context.user_data["current_relative"] = {}
    context.user_data["rel_field_sub"] = 0

    if spec.get("ask_gender"):
        await target.message.reply_text(
            T.GENDER_PROMPT[lang],
            reply_markup=kb([(T.BTN_GENDER_QIZ[lang], "gender_qiz"),
                              (T.BTN_GENDER_OGIL[lang], "gender_ogil")]),
        )
    else:
        await ask_relative_field(target, context)


async def ask_relative_field(target, context: ContextTypes.DEFAULT_TYPE):
    lang = lang_of(context)
    spec = _current_spec(context)
    sub = context.user_data["rel_field_sub"]
    field_keys = ["fio", "tug", "ish", "turar"]
    fkey = field_keys[sub]

    if fkey == "turar":
        shared = shared_address_for(spec["key"], context)
        if shared:
            await relative_save_field(target, context, shared)
            return

    label = context.user_data.get("current_relative_label")
    if not label:
        label = spec["label"][0] if lang == T.L else spec["label"][1]

    prompt = T.REL_FIELD_PROMPTS[fkey][lang].format(label=label)
    text = prompt + T.ASK_VOICE_HINT[lang]
    await target.message.reply_text(text)


async def on_presence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    spec = _current_spec(context)
    if spec is None:
        return

    if spec.get("is_spouse_gate"):
        context.user_data["has_spouse"] = (query.data == "presence_yes")
        if query.data == "presence_yes":
            await ask_spouse_gate(query, context)
        else:
            context.user_data["rel_cat_idx"] += 1
            await start_relative_category(query, context)
        return

    if query.data == "presence_yes":
        await begin_relative_entry(query, context)
    else:
        context.user_data["rel_cat_idx"] += 1
        await start_relative_category(query, context)


async def ask_spouse_gate(target, context: ContextTypes.DEFAULT_TYPE):
    lang = lang_of(context)
    await target.message.reply_text(
        T.SPOUSE_GATE_PROMPT[lang],
        reply_markup=kb([(T.BTN_YES[lang], "spgate_yes"), (T.BTN_NO[lang], "spgate_no")]),
    )


async def on_spouse_gate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = lang_of(context)
    if query.data == "spgate_yes":
        context.user_data["awaiting"] = "spouse_address"
        text = T.SHARED_ADDRESS_ASK[lang] + T.ASK_VOICE_HINT[lang]
        await query.message.reply_text(text)
    else:
        context.user_data["spouse_shared_address"] = None
        await begin_relative_entry(query, context)


async def on_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = lang_of(context)
    gkey = "qiz" if query.data == "gender_qiz" else "ogil"
    label_col = T.GENDER_LABELS[gkey][lang]
    context.user_data["current_relative_col"] = label_col
    spec = _current_spec(context)
    base_label = spec["label"][0] if lang == T.L else spec["label"][1]
    context.user_data["current_relative_label"] = f"{label_col} ({base_label.lower()})" if lang == T.L else f"{label_col} ({base_label.lower()})"
    await ask_relative_field(query, context)


async def relative_save_field(target, context: ContextTypes.DEFAULT_TYPE, text: str):
    lang = lang_of(context)
    spec = _current_spec(context)
    sub = context.user_data["rel_field_sub"]
    field_keys = ["fio", "tug", "ish", "turar"]
    fkey = field_keys[sub]
    if fkey == "fio":
        text = smart_capitalize_name(text)
    context.user_data["current_relative"][fkey] = text
    sub += 1

    if sub < 4:
        context.user_data["rel_field_sub"] = sub
        await ask_relative_field(target, context)
        return

    # yozuv tugadi -> ro'yxatga qo'shamiz
    entry = context.user_data["current_relative"]
    if spec.get("ask_gender"):
        col = context.user_data.get("current_relative_col", spec["label"][0])
    else:
        col = spec["col"][0] if lang == T.L else spec["col"][1]
    entry["col"] = col
    context.user_data["relatives"].append(entry)
    context.user_data["current_relative"] = {}
    context.user_data.pop("current_relative_label", None)
    context.user_data.pop("current_relative_col", None)
    context.user_data["rel_field_sub"] = 0

    if spec.get("multi"):
        label = spec["label"][0] if lang == T.L else spec["label"][1]
        await target.message.reply_text(
            _more_relative_prompt(lang, label),
            reply_markup=kb([(T.BTN_ADD_MORE[lang], "rel_more_yes"), (T.BTN_NO_MORE[lang], "rel_more_no")]),
        )
    else:
        context.user_data["rel_cat_idx"] += 1
        await start_relative_category(target, context)


def _more_relative_prompt(lang, label):
    if lang == T.L:
        return f"Yana {label.lower()} (shu toifadan) qo'shasizmi?"
    return f"Яна {label.lower()} (шу тоифадан) қўшасизми?"


async def on_relative_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "rel_more_yes":
        await begin_relative_entry(query, context)
    else:
        context.user_data["rel_cat_idx"] += 1
        await start_relative_category(query, context)


# ============================== RASM VA YAKUN =================================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = lang_of(context)
    if context.user_data.get("phase") != "photo":
        return

    if "data" not in context.user_data:
        # Sessiya (masalan server qayta ishga tushgani sababli) yo'qolgan
        await update.message.reply_text(T.SESSION_LOST_MSG[lang])
        context.user_data.clear()
        return

    photo_path = None
    out_path = None
    try:
        photo = update.message.photo[-1]
        tg_file = await context.bot.get_file(photo.file_id)
        photo_path = os.path.join(TMP_DIR, f"{uuid.uuid4().hex}.jpg")
        await tg_file.download_to_drive(photo_path)

        await update.message.reply_text(T.GENERATING[lang])

        out_path = build_document(
            lang=lang,
            data=context.user_data["data"],
            mehnat=context.user_data["mehnat"],
            relatives=context.user_data["relatives"],
            photo_path=photo_path,
        )

        with open(out_path, "rb") as f:
            await update.message.reply_document(f, filename=os.path.basename(out_path))

        await update.message.reply_text(T.DONE_MSG[lang])
        context.user_data["phase"] = "done"
    except Exception:
        logger.exception("Hujjat tayyorlashda xatolik")
        await update.message.reply_text(T.DOC_ERROR_MSG[lang])
    finally:
        for p in (photo_path, out_path):
            if p:
                try:
                    os.remove(p)
                except OSError:
                    pass


async def on_error(update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Kutilmagan xatolik: %s", context.error, exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_message:
            lang = lang_of(context)
            await update.effective_message.reply_text(T.GENERIC_ERROR_MSG[lang])
    except Exception:
        pass


async def photo_phase_wrong_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("phase") == "photo":
        lang = lang_of(context)
        await update.message.reply_text(T.PHOTO_WAIT_HINT[lang])


# ============================== MAIN =========================================

async def health(request):
    return web.Response(text="OK")


async def telegram_webhook_handler(request):
    application = request.app["telegram_app"]
    data = await request.json()
    update = Update.de_json(data, application.bot)
    # Telegram'ga darhol "OK" javobini qaytaramiz, so'ng update'ni fonda
    # qayta ishlaymiz. Aks holda ovozni tanish/hujjat tayyorlash vaqt olgani
    # uchun Telegram javobni kutmasdan bir xil xabarni qayta-qayta yuborishi
    # (va shu orqali sessiya holatida g'alati chalkashliklar chiqishi) mumkin edi.
    asyncio.create_task(_process_update_safely(application, update))
    return web.Response(text="OK")


async def _process_update_safely(application: Application, update: Update):
    try:
        await application.process_update(update)
    except Exception:
        logger.exception("Update'ni qayta ishlashda xatolik")


async def run_webhook_mode(application: Application):
    await application.initialize()
    await application.start()

    webhook_url = f"{WEBHOOK_HOST}/{BOT_TOKEN}"
    try:
        await application.bot.set_webhook(url=webhook_url)
        logger.info("Webhook o'rnatildi: %s", webhook_url)
    except Exception as e:
        logger.error(
            "Webhookni o'rnatib bo'lmadi (%s). WEBHOOK_HOST hali to'g'ri "
            "domenga o'zgartirilmagan bo'lishi mumkin — Render'da to'g'ri "
            "qiymatga o'zgartirib, qayta deploy qiling.", e,
        )

    aio_app = web.Application()
    aio_app["telegram_app"] = application
    aio_app.router.add_get("/", health)
    aio_app.router.add_post(f"/{BOT_TOKEN}", telegram_webhook_handler)

    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info("Webhook server %s portda ishga tushdi", PORT)

    # Dastur to'xtamasdan ishlab tursin
    while True:
        await asyncio.sleep(3600)


def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))

    app.add_handler(CallbackQueryHandler(on_lang_choice, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(on_quick_no, pattern="^quickno$"))
    app.add_handler(CallbackQueryHandler(on_confirm, pattern="^confirm$"))
    app.add_handler(CallbackQueryHandler(on_edit, pattern="^edit$"))
    app.add_handler(CallbackQueryHandler(on_mehnat_more, pattern="^mehnat_more_"))
    app.add_handler(CallbackQueryHandler(on_family_gate, pattern="^famgate_"))
    app.add_handler(CallbackQueryHandler(on_spouse_gate, pattern="^spgate_"))
    app.add_handler(CallbackQueryHandler(on_presence, pattern="^presence_"))
    app.add_handler(CallbackQueryHandler(on_gender, pattern="^gender_"))
    app.add_handler(CallbackQueryHandler(on_relative_more, pattern="^rel_more_"))

    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(
        filters.Document.ALL & ~filters.COMMAND, photo_phase_wrong_type
    ))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(on_error)
    return app


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. .env faylga BOT_TOKEN=... deb yozing "
            "(.env.example faylga qarang)."
        )

    application = build_application()

    if WEBHOOK_HOST:
        logger.info("WEBHOOK rejimida ishga tushmoqda (Render va h.k. uchun)...")
        asyncio.run(run_webhook_mode(application))
    else:
        logger.info("POLLING rejimida ishga tushmoqda (uy kompyuteri/VPS uchun)...")
        application.run_polling()


if __name__ == "__main__":
    main()
