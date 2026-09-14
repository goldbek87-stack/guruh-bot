"""
Botning barcha buyruq va xabar ishlovchilari (handlers).

Yangi qoida qo'shish kerak bo'lsa (masalan reklama so'zlarini bloklash),
odatda shu faylga yangi funksiya yozib, bot.py da ro'yxatdan o'tkazasiz.
"""

import time
import asyncio
import logging

from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes

import config
import database as db
import filters

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


def _limit_for(user_id: int) -> int:
    invites = db.get_invite_count(user_id)
    invite_bonus = (invites // config.INVITES_PER_BONUS) * config.BONUS_MESSAGES
    paid_bonus = db.get_paid_bonus(user_id)
    return config.DAILY_MESSAGE_LIMIT + invite_bonus + paid_bonus


def _limit_reached_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Do'st taklif qilish", callback_data="show_invite")],
        [InlineKeyboardButton("💳 To'lov qilish", callback_data="show_payment")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Men guruh nazoratchi botiman.\n\n"
        "/mening_havolam - shaxsiy taklif havolangizni olish\n"
        "/statistikam - bugungi statistikangizni ko'rish\n"
        "/tolov - to'lov qilib limit oshirish"
    )


async def _build_invite_text(chat, user, context) -> str:
    db.ensure_user(user.id, user.username)

    link = db.get_link_by_owner(user.id)
    if not link:
        invite = await context.bot.create_chat_invite_link(
            chat_id=chat.id,
            name=f"ref-{user.id}",
        )
        link = invite.invite_link
        db.save_invite_link(link, user.id)

    invites = db.get_invite_count(user.id)
    limit = _limit_for(user.id)
    return (
        f"Sizning shaxsiy taklif havolangiz:\n{link}\n\n"
        f"Hozircha siz orqali {invites} kishi qo'shilgan.\n"
        f"Joriy kunlik xabar limitingiz: {limit} ta "
        f"(har {config.INVITES_PER_BONUS} taklif uchun +{config.BONUS_MESSAGES} ta bonus)."
    )


async def my_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    try:
        text = await _build_invite_text(chat, user, context)
    except Exception:
        logger.exception("Invite link yaratib bo'lmadi")
        await update.message.reply_text(
            "Havola yaratib bo'lmadi. Botga guruhda 'Foydalanuvchilarni "
            "taklif qilish orqali havola yaratish' huquqi berilganini tekshiring."
        )
        return
    await update.message.reply_text(text)


def _payment_instructions() -> str:
    return (
        f"To'lov orqali kunlik limitingizni oshirishingiz mumkin.\n\n"
        f"💳 Karta raqami: {config.CARD_NUMBER}\n"
        f"👤 Karta egasi: {config.CARD_HOLDER_NAME}\n"
        f"💰 Summa: {config.PAYMENT_AMOUNT_TEXT}\n\n"
        f"To'lovni amalga oshirgach, chek (skrinshot)ni shu yerga, botning "
        f"shaxsiy xabarlariga (shu chatga) rasm qilib yuboring. Admin tekshirib "
        f"tasdiqlagach, limitingizga +{config.PAYMENT_BONUS_MESSAGES} ta xabar qo'shiladi."
    )


async def pay_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/tolov buyrug'i - to'lov ma'lumotlarini istalgan vaqtda ko'rsatadi."""
    if update.effective_chat.type != "private":
        try:
            await context.bot.send_message(update.effective_user.id, _payment_instructions())
            await update.message.reply_text(
                "To'lov ma'lumotlarini shaxsiy xabaringizga yubordim."
            )
        except Exception:
            await update.message.reply_text(
                f"Iltimos, avval botga shaxsiy yozing: "
                f"https://t.me/{context.bot.username} keyin /tolov buyrug'ini qayta yuboring."
            )
        return
    await update.message.reply_text(_payment_instructions())


async def limit_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruhda 'Do'st taklif qilish' / 'To'lov qilish' tugmalari bosilganda ishlaydi."""
    query = update.callback_query
    user = query.from_user
    chat = query.message.chat if query.message else None
    await query.answer()

    if query.data == "show_invite":
        try:
            text = await _build_invite_text(chat, user, context)
        except Exception:
            logger.exception("Invite link yaratib bo'lmadi")
            await query.answer(
                "Havola yaratib bo'lmadi. Bot admin huquqlarini tekshiring.",
                show_alert=True,
            )
            return
        try:
            await context.bot.send_message(user.id, text)
            await query.answer("Taklif havolangizni shaxsiy xabaringizga yubordim.", show_alert=True)
        except Exception:
            await query.answer(
                f"Avval botga shaxsiy yozing: https://t.me/{context.bot.username}",
                show_alert=True,
            )

    elif query.data == "show_payment":
        try:
            await context.bot.send_message(user.id, _payment_instructions())
            await query.answer("To'lov ma'lumotlarini shaxsiy xabaringizga yubordim.", show_alert=True)
        except Exception:
            await query.answer(
                f"Avval botga shaxsiy yozing: https://t.me/{context.bot.username}",
                show_alert=True,
            )


async def receive_payment_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi botga shaxsiy chatda to'lov skrinshotini yuborganda ishlaydi."""
    user = update.effective_user
    message = update.effective_message
    if not message.photo:
        return

    db.ensure_user(user.id, user.username)
    photo_file_id = message.photo[-1].file_id
    payment_id = db.create_pending_payment(user.id, user.username, photo_file_id)

    await message.reply_text(
        "Chekingiz qabul qilindi. Admin tekshirib tasdiqlagach, limitingiz avtomatik oshadi."
    )

    caption = (
        f"💳 Yangi to'lov so'rovi (#{payment_id})\n"
        f"Foydalanuvchi: @{user.username or user.id} (ID: {user.id})\n"
        f"Summa: {config.PAYMENT_AMOUNT_TEXT}"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve:{payment_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"reject:{payment_id}"),
    ]])
    for admin_id in config.ADMIN_IDS:
        try:
            await context.bot.send_photo(
                admin_id, photo=photo_file_id, caption=caption, reply_markup=keyboard
            )
        except Exception:
            logger.warning(f"Adminga ({admin_id}) to'lov so'rovini yuborib bo'lmadi")


async def payment_decision_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin 'Tasdiqlash'/'Rad etish' tugmasini bosganda ishlaydi."""
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("Bu tugma faqat adminlar uchun.", show_alert=True)
        return

    action, payment_id_str = query.data.split(":")
    payment_id = int(payment_id_str)
    payment = db.get_payment(payment_id)

    if payment is None:
        await query.answer("So'rov topilmadi.", show_alert=True)
        return

    if payment["status"] != "pending":
        await query.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    if action == "approve":
        changed = db.set_payment_status(payment_id, "approved")
        if not changed:
            await query.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
            return
        db.add_paid_bonus(payment["user_id"], config.PAYMENT_BONUS_MESSAGES)
        await query.answer("Tasdiqlandi.")
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✅ TASDIQLANDI"
        )
        try:
            await context.bot.send_message(
                payment["user_id"],
                f"To'lovingiz tasdiqlandi! Kunlik limitingizga "
                f"+{config.PAYMENT_BONUS_MESSAGES} ta xabar qo'shildi.",
            )
        except Exception:
            pass
    else:
        changed = db.set_payment_status(payment_id, "rejected")
        if not changed:
            await query.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
            return
        await query.answer("Rad etildi.")
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ RAD ETILDI"
        )
        try:
            await context.bot.send_message(
                payment["user_id"],
                "To'lovingiz tasdiqlanmadi. Chek noaniq bo'lsa, aniqroq skrinshot "
                "bilan qayta urinib ko'ring yoki admin bilan bog'laning.",
            )
        except Exception:
            pass


async def group_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruh ichida yozilganda, guruhning raqamli ID'sini chiqaradi -
    shuni config.py dagi TARGET_GROUP_ID ga qo'yasiz."""
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Bu buyruqni guruh ichida yozing.")
        return
    await update.message.reply_text(
        f"Bu guruhning ID raqami:\n{chat.id}\n\n"
        f"Shu raqamni config.py faylidagi TARGET_GROUP_ID ga qo'ying."
    )


def _staged_preview_text(text: str) -> str:
    text = text or "(matnsiz e'lon)"
    if len(text) > 500:
        text = text[:500] + "..."
    return f"📋 Joylashga tayyor e'lon:\n\n{text}"


def _staged_keyboard(staged_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Guruhga joylash", callback_data=f"stagepost:{staged_id}"),
        InlineKeyboardButton("🗑 Bekor qilish", callback_data=f"stagecancel:{staged_id}"),
    ]])


async def admin_forward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin botga shaxsiy chatda forward qilgan (yoki oddiy yozgan) e'lonni
    navbatga qo'yadi va joylash uchun tugma chiqaradi. Bir vaqtda 10-30 ta
    xabar forward qilinsa ham, Telegram ularni birma-bir yuboradi - shu
    yerda har biriga alohida javob beriladi, ortidan kichik pauza qo'yiladi
    (Telegram'ning "juda tez xabar" cheklovidan qochish uchun)."""
    message = update.effective_message
    admin = update.effective_user

    text = message.text or message.caption or ""
    photo_file_id = message.photo[-1].file_id if message.photo else None

    if not text and not photo_file_id:
        return  # tushunarsiz turdagi xabar - e'tiborsiz qoldiramiz

    staged_id = db.create_staged_post(admin.id, text, photo_file_id)
    preview = _staged_preview_text(text)
    keyboard = _staged_keyboard(staged_id)

    try:
        if photo_file_id:
            await context.bot.send_photo(
                admin.id, photo=photo_file_id, caption=preview, reply_markup=keyboard
            )
        else:
            await context.bot.send_message(admin.id, preview, reply_markup=keyboard)
    except Exception:
        logger.exception("Admin uchun staged post preview yuborib bo'lmadi")

    # Ko'p xabar birdan forward qilinganda Telegram'ni "flood" qilib qo'ymaslik uchun
    await asyncio.sleep(0.35)


async def staged_post_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'Guruhga joylash' / 'Bekor qilish' tugmalari bosilganda ishlaydi."""
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("Bu tugma faqat adminlar uchun.", show_alert=True)
        return

    action, staged_id_str = query.data.split(":")
    staged_id = int(staged_id_str)
    staged = db.get_staged_post(staged_id)

    if staged is None:
        await query.answer("Yozuv topilmadi.", show_alert=True)
        return

    if staged["status"] != "pending":
        await query.answer("Bu e'lon allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    if action == "stagepost":
        if not config.TARGET_GROUP_ID:
            await query.answer(
                "TARGET_GROUP_ID hali config.py da sozlanmagan. Guruhda /guruh_id yozib "
                "chiqqan raqamni config.py ga qo'ying.",
                show_alert=True,
            )
            return

        changed = db.set_staged_status(staged_id, "posted")
        if not changed:
            await query.answer("Bu e'lon allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        try:
            if staged["photo_file_id"]:
                await context.bot.send_photo(
                    config.TARGET_GROUP_ID,
                    photo=staged["photo_file_id"],
                    caption=staged["text"] or None,
                )
            else:
                await context.bot.send_message(config.TARGET_GROUP_ID, staged["text"])
            await query.answer("Guruhga joylandi.")
            if query.message.caption is not None:
                await query.edit_message_caption(caption=query.message.caption + "\n\n✅ JOYLANDI")
            else:
                await query.edit_message_text(query.message.text + "\n\n✅ JOYLANDI")
        except Exception:
            logger.exception("Guruhga joylab bo'lmadi")
            db.set_staged_status(staged_id, "pending")  # qayta urinish imkoni qolsin
            await query.answer(
                "Guruhga joylab bo'lmadi. Botda guruhda yozish huquqi bormi, "
                "TARGET_GROUP_ID to'g'rimi - tekshiring.",
                show_alert=True,
            )
    else:  # stagecancel
        changed = db.set_staged_status(staged_id, "cancelled")
        if not changed:
            await query.answer("Bu e'lon allaqachon ko'rib chiqilgan.", show_alert=True)
            return
        await query.answer("Bekor qilindi.")
        if query.message.caption is not None:
            await query.edit_message_caption(caption=query.message.caption + "\n\n🗑 BEKOR QILINDI")
        else:
            await query.edit_message_text(query.message.text + "\n\n🗑 BEKOR QILINDI")


async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.ensure_user(user.id, user.username)
    sent = db.get_message_count(user.id)
    invites = db.get_invite_count(user.id)
    limit = _limit_for(user.id)
    await update.message.reply_text(
        f"Bugun yozgan xabarlaringiz: {sent}/{limit}\n"
        f"Taklif qilgan odamlaringiz: {invites}"
    )


async def admin_ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    inviters = db.top_inviters(10)
    writers = db.top_writers_today(10)

    lines = ["Eng ko'p taklif qilganlar:"]
    if inviters:
        for i, row in enumerate(inviters, 1):
            name = row["username"] or row["user_id"]
            lines.append(f"{i}. @{name} - {row['invite_count']} ta")
    else:
        lines.append("Hali ma'lumot yo'q.")

    lines.append("")
    lines.append("Bugun eng faol yozganlar:")
    if writers:
        for i, row in enumerate(writers, 1):
            name = row["username"] or row["user_id"]
            lines.append(f"{i}. @{name} - {row['message_count']} ta")
    else:
        lines.append("Hali ma'lumot yo'q.")

    await update.message.reply_text("\n".join(lines))


async def track_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cm = update.chat_member
    if cm is None:
        return

    old_status = cm.old_chat_member.status
    new_status = cm.new_chat_member.status
    joined = (
        old_status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED, ChatMemberStatus.RESTRICTED)
        and new_status == ChatMemberStatus.MEMBER
    )
    if not joined:
        return

    link_obj = cm.invite_link
    if link_obj is None:
        return  # oddiy (umumiy) link orqali kirgan - kim taklif qilganini bilib bo'lmaydi

    owner_id = db.get_owner_by_link(link_obj.invite_link)
    if owner_id:
        db.add_invite(owner_id)
        try:
            await context.bot.send_message(
                owner_id,
                "Sizning havolangiz orqali guruhga yangi a'zo qo'shildi. Rahmat!",
            )
        except Exception:
            pass  # foydalanuvchi botni bloklagan bo'lishi mumkin


async def moderate_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    if message is None or user is None or user.is_bot:
        return

    db.ensure_user(user.id, user.username)

    if is_admin(user.id):
        return  # adminlar limit va filtrlardan ozod

    # 1) Taqiqlangan link tekshiruvi (boshqa guruh/kanal, ijtimoiy tarmoq)
    blocked_url = filters.find_blocked_link(message)
    if blocked_url:
        try:
            await message.delete()
        except Exception:
            logger.warning("Xabarni o'chirib bo'lmadi - botda admin huquqi yo'qmi?")

        warnings = db.add_warning(user.id)
        if warnings >= config.WARNINGS_BEFORE_MUTE:
            until = int(time.time()) + config.MUTE_MINUTES * 60
            try:
                await context.bot.restrict_chat_member(
                    chat_id=message.chat_id,
                    user_id=user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until,
                )
                await context.bot.send_message(
                    message.chat_id,
                    f"{user.first_name} boshqa guruh/tarmoq linki tashlashda davom etgani "
                    f"uchun {config.MUTE_MINUTES} daqiqaga yozishdan cheklandi.",
                )
            except Exception:
                logger.warning("Foydalanuvchini cheklab bo'lmadi")
            db.reset_warnings(user.id)
        else:
            try:
                await context.bot.send_message(
                    message.chat_id,
                    f"{user.first_name}, guruhda boshqa guruh/kanal yoki ijtimoiy tarmoq "
                    f"linklarini tashlash mumkin emas. ({warnings}/{config.WARNINGS_BEFORE_MUTE} "
                    f"ogohlantirish)",
                )
            except Exception:
                pass
        return

    # 2) Kunlik xabar limiti tekshiruvi
    count = db.increment_message_count(user.id)
    limit = _limit_for(user.id)

    if count > limit:
        try:
            await message.delete()
        except Exception:
            logger.warning("Xabarni o'chirib bo'lmadi")
        try:
            await context.bot.send_message(
                message.chat_id,
                f"{user.first_name}, bugungi kunlik limitingiz ({limit} ta xabar) tugadi.\n"
                f"Ko'proq yozish uchun quyidagilardan birini tanlang:",
                reply_markup=_limit_reached_keyboard(),
            )
        except Exception:
            pass
