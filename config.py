# ============ SOZLAMALAR ============
# Botni ishga tushirishdan oldin shu yerdagi qiymatlarni to'ldiring.

# @BotFather dan olgan tokeningiz
BOT_TOKEN = "8968361488:AAGscTKDd_-tts-vPWFYEaVRrn_Ec-UyDa0"

# Guruh adminlarining Telegram user_id raqamlari (limit va filtrlardan ozod bo'ladi).
# O'z user_id raqamingizni bilish uchun Telegramda @userinfobot ga /start yozing.
ADMIN_IDS = [
    660625875,  # Farrux
]

# Kuniga har bir oddiy a'zo yubora oladigan bepul xabarlar soni
DAILY_MESSAGE_LIMIT = 5

# Necha kishi taklif qilsa (guruhga qo'shsa), bonus limit qo'shiladi
INVITES_PER_BONUS = 10
BONUS_MESSAGES = 5

# Necha marta ogohlantirilgandan keyin vaqtincha yoza olmaydigan (mute) qilinadi
WARNINGS_BEFORE_MUTE = 3
MUTE_MINUTES = 60

# Taqiqlangan domenlar - shu manzillarga link tashlansa, xabar avtomatik o'chiriladi
BLOCKED_DOMAINS = [
    "t.me",
    "telegram.me",
    "instagram.com",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "facebook.com",
    "fb.watch",
    "wa.me",
    "whatsapp.com",
]

# Sizning guruhingizning username'i (@ belgisisiz).
# Bu kiritilsa, o'z guruh linkini yozish bloklanmaydi (t.me/shu_username istisno bo'ladi).
OWN_GROUP_USERNAME = "sizning_guruh_username"

# ============ TO'LOV SOZLAMALARI ============
# Kunlik limitni pul to'lab ham oshirish mumkin bo'lsin desangiz, shu qismni to'ldiring.
# Bot to'lovni o'zi tekshirmaydi - foydalanuvchi skrinshot yuboradi, admin ko'rib
# tasdiqlaydi (tugmani bosish orqali), shundan keyingina bonus limit qo'shiladi.

# Pul qabul qilinadigan plastik karta raqami
CARD_NUMBER = "0000 0000 0000 0000"

# Karta egasining ismi (ba'zi bank ilovalari o'tkazmada buni so'raydi)
CARD_HOLDER_NAME = "F.I.Sh."

# Narxi - foydalanuvchiga shunday matn ko'rsatiladi
PAYMENT_AMOUNT_TEXT = "20 000 so'm"

# Bitta tasdiqlangan to'lov necha ta qo'shimcha kunlik xabar beradi
PAYMENT_BONUS_MESSAGES = 20

# ============ BOSHQA MANBALARDAN E'LON JOYLASH ============
# Admin botga (shaxsiy xabarda) forward qilgan/yuborgan xabarlarni asosiy
# guruhga bitta tugma bosish bilan joylash uchun kerak.
#
# Qiymatini bilish uchun: botni guruhga admin qilib qo'shgach, guruh ichida
# /guruh_id buyrug'ini yozing - bot sizga shu yerga qo'yiladigan raqamni beradi.
TARGET_GROUP_ID = 0  # <- guruh_id buyrug'i chiqargan raqamni shu yerga qo'ying
