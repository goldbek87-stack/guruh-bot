"""
Botni ishga tushiruvchi asosiy fayl.

Ishga tushirish:
    python bot.py

Ishga tushirishdan oldin config.py faylini to'ldiring
(BOT_TOKEN, ADMIN_IDS va h.k.).
"""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    CallbackQueryHandler,
    filters as tg_filters,
)

import config
import database as db
import handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def main():
    db.init_db()

    app = Application.builder().token(config.BOT_TOKEN).build()

    # Buyruqlar
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("mening_havolam", handlers.my_link))
    app.add_handler(CommandHandler("statistikam", handlers.my_stats))
    app.add_handler(CommandHandler("reyting", handlers.admin_ranking))
    app.add_handler(CommandHandler("tolov", handlers.pay_info))
    app.add_handler(CommandHandler("guruh_id", handlers.group_id_command))

    # Yangi a'zo qo'shilganda - kim taklif qilganini aniqlash
    app.add_handler(ChatMemberHandler(handlers.track_new_members, ChatMemberHandler.CHAT_MEMBER))

    # "Do'st taklif qilish" / "To'lov qilish" tugmalari (guruhda chiqadi)
    app.add_handler(CallbackQueryHandler(handlers.limit_menu_callback, pattern="^show_"))
    # Admin uchun "Tasdiqlash" / "Rad etish" tugmalari (to'lov cheklarida)
    app.add_handler(CallbackQueryHandler(handlers.payment_decision_callback, pattern="^(approve|reject):"))
    # Admin uchun "Guruhga joylash" / "Bekor qilish" tugmalari (forward qilingan e'lonlarda)
    app.add_handler(CallbackQueryHandler(handlers.staged_post_callback, pattern="^stage(post|cancel):"))

    # Admin botga shaxsiy chatda forward qilgan/yozgan e'lonlar (boshqa guruh/OLX'dan
    # qo'lda ko'chirilgan) - MUHIM: bu handler quyidagi oddiy to'lov-skrinshot
    # handleridan OLDIN turishi kerak, aks holda adminning forwardlari ham
    # to'lov skrinshoti sifatida qabul qilinib qoladi.
    app.add_handler(
        MessageHandler(
            (tg_filters.TEXT | tg_filters.PHOTO)
            & tg_filters.ChatType.PRIVATE
            & tg_filters.User(user_id=config.ADMIN_IDS)
            & ~tg_filters.COMMAND,
            handlers.admin_forward_handler,
        )
    )

    # Botga shaxsiy (DM) yuborilgan to'lov skrinshotlari (admin bo'lmagan foydalanuvchilardan)
    app.add_handler(
        MessageHandler(
            tg_filters.PHOTO & tg_filters.ChatType.PRIVATE,
            handlers.receive_payment_photo,
        )
    )

    # Guruhdagi barcha oddiy xabarlarni nazorat qilish (link va limit tekshiruvi)
    app.add_handler(
        MessageHandler(
            (tg_filters.TEXT | tg_filters.CAPTION | tg_filters.PHOTO | tg_filters.VIDEO)
            & ~tg_filters.COMMAND
            & tg_filters.ChatType.GROUPS,
            handlers.moderate_message,
        )
    )

    # Telegramning o'zi chiqaradigan "qo'shildi" / "chiqarildi" tizim xabarlarini
    # bir necha soniyadan keyin o'chirish (guruh ortiqcha to'lib ketmasligi uchun)
    app.add_handler(
        MessageHandler(
            tg_filters.StatusUpdate.NEW_CHAT_MEMBERS | tg_filters.StatusUpdate.LEFT_CHAT_MEMBER,
            handlers.delete_service_message,
        )
    )

    logging.info("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
