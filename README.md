# Guruh nazoratchi bot

Bu bot uy-joy oldi-sotdi/ijara guruhingiz uchun quyidagilarni avtomatik qiladi:

- Har bir a'zoning shaxsiy taklif havolasi orqali **necha kishi qo'shganini** hisoblaydi
  (ham havola orqali o'zi kirgan, ham kimdir uni guruhga qo'lda qo'shgan holatlarning
  ikkalasi ham hisoblanadi). `/mening_havolam` va `/statistikam` buyruqlari guruhda
  yozilsa ham, javob har doim shaxsiy xabarga (DM) yuboriladi - guruhda faqat qisqa
  "yubordim" degan xabar qoladi, boshqalarga chalkash ko'rinmaydi.
- Har bir a'zoning **kunlik yozgan xabarlar sonini** hisoblaydi va standart limit (5 ta/kun)dan
  oshsa xabarni o'chiradi; har 10 ta taklif uchun +5 ta bonus limit qo'shiladi
- **Boshqa guruh/kanal va ijtimoiy tarmoq linklarini** (Instagram, YouTube, TikTok, Facebook, va h.k.)
  avtomatik o'chiradi, 3 marta takrorlansa foydalanuvchini 1 soatga cheklaydi (mute)
- Limitdan oshgan foydalanuvchiga **"Do'st taklif qilish" yoki "To'lov qilish"** tugmalarini
  ko'rsatadi; to'lovni tanlasa karta raqami botning shaxsiy xabarida (DM) yuboriladi, u yerga
  chek (skrinshot) tashlaydi, bot buni tugmalar bilan adminga jo'natadi, admin bosib
  tasdiqlasa foydalanuvchiga avtomatik bonus limit qo'shiladi
- Guruh adminlari barcha cheklovlardan ozod
- **Boshqa joydan (OLX, boshqa guruh) qo'lda ko'chirilgan e'lonlarni tezroq joylash:**
  admin botga shaxsiy chatda xabar forward qilsa yoki matn/rasm yuborsa, bot uni
  "✅ Guruhga joylash" / "🗑 Bekor qilish" tugmalari bilan qaytaradi — bitta tugma
  bosish bilan asosiy guruhga joylanadi. Bir vaqtda 10-30 tagacha xabarni forward
  qilsangiz ham, bot ularning har birini alohida navbatga qo'yadi va sizga har biri
  uchun alohida tugma chiqaradi — qaysi birini joylash, qaysi birini (masalan
  eskirgan bo'lsa) bekor qilishni **o'zingiz tanlaysiz**.

Kodni kengaytirish oson: `filters.py` ga yangi qoida, `handlers.py` ga yangi buyruq
qo'shib boraverasiz — qolgan qism o'zgarmaydi.

## 1-qadam: Bot yaratish

1. Telegramda **@BotFather** ga yozing, `/newbot` buyrug'ini yuboring, nom va username bering.
2. BotFather bergan **tokenni** saqlab qo'ying.
3. BotFather'da `/setprivacy` → botingizni tanlang → **Disable** qiling. Bu bot guruhdagi
   **barcha** xabarlarni ko'rishi (xabar sonini hisoblashi) uchun shart. (Agar botni guruhda
   admin qilsangiz, bu qadam shart emas — admin bo'lgan bot baribir barcha xabarni ko'radi.)

## 2-qadam: Botni guruhga qo'shish va admin qilish

Botni guruhingizga qo'shing va **admin** qiling, quyidagi huquqlarni albatta yoqing:

- Delete messages (Xabarlarni o'chirish)
- Ban/Restrict users (Foydalanuvchilarni cheklash)
- Invite users via link (Havola orqali taklif qilish)

## 3-qadam: Sozlash

`config.py` faylini oching va to'ldiring:

- `BOT_TOKEN` — BotFather bergan token
- `ADMIN_IDS` — o'zingiz va boshqa adminlarning Telegram user_id raqamlari
  (bilish uchun **@userinfobot** ga `/start` yozing)
- `OWN_GROUP_USERNAME` — guruhingiz username'i (agar guruh public bo'lsa)
- `CARD_NUMBER`, `CARD_HOLDER_NAME`, `PAYMENT_AMOUNT_TEXT`, `PAYMENT_BONUS_MESSAGES` —
  to'lov qabul qilish uchun karta ma'lumotlaringiz va narx
- `TARGET_GROUP_ID` — botni guruhga qo'shib bo'lgach, guruh ichida `/guruh_id` deb
  yozing, bot chiqargan raqamni shu yerga qo'ying (boshqa joydan ko'chirilgan
  e'lonlarni to'g'ri guruhga joylashi uchun kerak)
- Kerak bo'lsa `DAILY_MESSAGE_LIMIT`, `BLOCKED_DOMAINS` va boshqa raqamlarni o'zgartiring

### To'lov qanday ishlaydi

1. Foydalanuvchi kunlik limitidan oshsa (yoki o'zi `/tolov` yozsa), unga karta raqami va
   summasi ko'rsatiladi.
2. U pulni o'tkazib, chekning skrinshotini **botga shaxsiy xabar sifatida** (guruhga emas!)
   yuboradi.
3. Bot skrinshotni barcha `ADMIN_IDS`'ga "✅ Tasdiqlash" / "❌ Rad etish" tugmalari bilan
   jo'natadi.
4. Admin "✅ Tasdiqlash"ni bossa, foydalanuvchining kunlik limitiga avtomatik
   `PAYMENT_BONUS_MESSAGES` ta xabar qo'shiladi va unga xabar boradi.

### Boshqa manbadan (OLX, boshqa guruh) e'lon joylash qanday ishlaydi

1. OLX'dagi yoki boshqa guruhdagi e'lonni ko'chirib olasiz (yoki to'g'ridan-to'g'ri
   xabarni botga forward qilasiz) va botga **shaxsiy chatda** yuborasiz.
2. Bot sizga o'sha e'lonning qisqa ko'rinishini "✅ Guruhga joylash" / "🗑 Bekor qilish"
   tugmalari bilan qaytaradi.
3. Joylashdan oldin, iloji bo'lsa, e'lon hali dolzarbligini (sotilmaganini) tekshirib
   oling — aks holda eskirgan e'lon guruhingizga ishonchni pasaytirishi mumkin.
4. "✅ Guruhga joylash" bossangiz, u darhol asosiy guruhga (`TARGET_GROUP_ID`) joylanadi.

**Eslatma:** agar bitta e'lon bir nechta rasmdan (albom) iborat bo'lsa, bot hozircha
har bir rasmni alohida e'lon sifatida navbatga qo'yadi (bittalab joylashingiz kerak
bo'ladi). Buni ham albomlarni birlashtiradigan qilib takomillashtirish mumkin —
kerak bo'lsa ayting.

**Muhim (avtomatlashtirish haqida):** bu funksiya ataylab **yarim-avtomatik** qilib
qurilgan — ya'ni har bir e'lonni siz ko'rib, tanlab joylaysiz. OLX'dan yoki boshqa
guruhlardan xabarlarni **to'liq avtomatik** (botning o'zi doimiy kuzatib, so'rovsiz
ko'chirib turadigan) qilish odatda o'sha platformalarning foydalanish shartlariga
zid va texnik jihatdan beqaror (hisob/IP bloklanishi mumkin) bo'lgani uchun,
bunday to'liq avtomatlashtirish shu loyihaga qo'shilmagan.

**Muhim:** bot to'lovni o'zi tekshirmaydi (bank hisobiga ulanmagan) — buni faqat admin
skrinshotga qarab qo'lda hal qiladi. Shaxsiy kartaga muntazam pul qabul qilish
O'zbekistonda qanday soliq/tadbirkorlik talablariga tushishi mumkinligini oldindan
tekshirib olishni maslahat beraman (men huquqiy/moliyaviy maslahat bera olmayman) —
hajm oshsa, keyinchalik Payme/Click/Uzum kabi rasmiy to'lov tizimiga o'tish ham mumkin.

## 4-qadam: Kompyuteringizda sinab ko'rish

```bash
pip install -r requirements.txt
python bot.py
```

Guruhda `/mening_havolam` va `/statistikam` buyruqlarini yozib tekshiring.
Terminalda `Ctrl+C` bosib to'xtatishingiz mumkin.

## 5-qadam: 24/7 ishlashi uchun joylashtirish (deploy)

Sinov muvaffaqiyatli bo'lsa, botni doim yoqilgan holda ushlab turadigan joyga
joylashtirish kerak (kompyuteringizni doim yoqib qo'yish shart emas). Ikkita tavsiya:

### A. Railway.app (eng oson, tez ishga tushadi)

Railway'ning bepul tarifi oylik kredit beradi (kichik botga odatda yetadi):

1. https://railway.app saytida GitHub hisobingiz orqali ro'yxatdan o'ting.
2. Ushbu papkani (`guruh_bot`) o'zingizning GitHub repositoriyingizga yuklang.
3. Railway'da **New Project → Deploy from GitHub repo** tanlang, repo'ni ko'rsating.
4. **Variables** bo'limida `BOT_TOKEN` kabi maxfiy qiymatlarni Environment
   Variable sifatida qo'yish tavsiya etiladi (config.py ichida token'ni bo'sh qoldirib,
   `os.environ["BOT_TOKEN"]` orqali o'qiydigan qilib o'zgartirsam ham bo'ladi — aytsangiz,
   shunday qilib beraman).
5. Deploy tugagach, loglarda "Bot ishga tushdi..." yozuvini ko'rasiz.

### B. Arzon VPS (eng ishonchli, uzoq muddatga)

Agar Railway'ning bepul krediti tugab qolishidan xavotir bo'lsangiz, oyiga ~$3-5
turadigan oddiy VPS (masalan Timeweb, Beget, Hostinger VPS) sotib olib, u yerda:

```bash
sudo apt update && sudo apt install python3-pip -y
pip install -r requirements.txt
nohup python3 bot.py &
```

buyrug'i bilan botni fon rejimida doimiy ishlatib qo'yasiz (yoki `systemd`/`screen`/`tmux`
orqali ishga tushirish tavsiya etiladi, chunki `nohup` server qayta ishga tushganda
botni avtomatik qayta yoqmaydi).

## Eslatma

`group_bot.db` fayli — barcha statistika saqlanadigan baza. Uni o'chirmang, aks holda
barcha hisoblar (kim nechta odam qo'shgani, ogohlantirishlar) yo'qoladi.
