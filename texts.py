# -*- coding: utf-8 -*-
"""
Barcha ikki tilli (lotin/kirill) matnlar, savol formulalari va
qarindoshlik rejasi shu yerda markazlashtirilgan — bot.py va doc_builder.py
shu yerdan foydalanadi.
"""

L = "lat"
C = "cyr"


def t(lang: str, lat_text: str, cyr_text: str) -> str:
    return lat_text if lang == L else cyr_text


TITLE = {L: "MA'LUMOTNOMA", C: "МАЪЛУМОТНОМА"}

# ---------------------------------------------------------------------------
# Oddiy (bitta javobli) savollar ro'yxati. Har biri: key, prompt(lat,cyr),
# label(lat,cyr — hujjatda "Label: qiymat" tarzida chiqadi), quick_no(bool)
# ---------------------------------------------------------------------------
SIMPLE_STEPS = [
    dict(
        key="fio",
        label=("F.I.SH.", "Ф.И.Ш."),
        prompt=(
            "To'liq F.I.SH.ingizni ayting (Familiya Ism Otasining ismi).\n"
            "Masalan: Oqilov Javlonbek Ikromjon o'g'li",
            "Тўлиқ Ф.И.Ш.ингизни айтинг (Фамилия Исм Отасининг исми).\n"
            "Масалан: Турғунов Фаррух Нуриддин ўғли",
        ),
        quick_no=False,
        is_header=True,
    ),
    dict(
        key="tug_yili",
        label=("Tug'ilgan yili", "Туғилган йили"),
        prompt=(
            "Tug'ilgan sanangizni ayting (kun.oy.yil). Masalan: 18.02.2005 yil",
            "Туғилган санангизни айтинг (кун.ой.йил). Масалан: 18.02.2005 йил",
        ),
        quick_no=False,
    ),
    dict(
        key="tug_joyi",
        label=("Tug'ilgan joyi", "Туғилган жойи"),
        prompt=(
            "Tug'ilgan joyingizni ayting (viloyat, shahar/tuman)",
            "Туғилган жойингизни айтинг (вилоят, шаҳар/туман)",
        ),
        quick_no=False,
    ),
    dict(
        key="millati",
        label=("Millati", "Миллати"),
        prompt=("Millatingizni ayting", "Миллатингизни айтинг"),
        quick_no=False,
    ),
    dict(
        key="partiya",
        label=("Partiyaviyligi", "Партиявийлиги"),
        prompt=(
            "Partiyaviyligingizni ayting (masalan: partiyasiz)",
            "Партиявийлигингизни айтинг (масалан: партиясиз)",
        ),
        quick_no=False,
    ),
    dict(
        key="malumoti",
        label=("Ma'lumoti", "Маълумоти"),
        prompt=(
            "Ma'lumotingiz darajasini ayting (masalan: oliy, o'rta maxsus)",
            "Маълумотингиз даражасини айтинг (масалан: олий, ўрта махсус)",
        ),
        quick_no=False,
    ),
    dict(
        key="tamomlagan",
        label=("Tamomlagan", "Тамомлаган"),
        prompt=(
            "Qaysi o'quv yurtini, qaysi yili tamomlaganingizni ayting",
            "Қайси ўқув юртини, қайси йили тамомлаганингизни айтинг",
        ),
        quick_no=False,
    ),
    dict(
        key="mutaxassis",
        label=("Ma'lumoti bo'yicha mutaxassisligi", "Маълумоти бўйича мутахассислиги"),
        prompt=(
            "Ma'lumotingiz bo'yicha mutaxassisligingizni ayting",
            "Маълумотингиз бўйича мутахассислигингизни айтинг",
        ),
        quick_no=False,
    ),
    dict(
        key="ilmiy_daraja",
        label=("Ilmiy darajasi", "Илмий даражаси"),
        prompt=(
            "Ilmiy darajangiz bormi? Bo'lsa ayting, bo'lmasa pastdagi tugmani bosing",
            "Илмий даражангиз борми? Бўлса айтинг, бўлмаса пастдаги тугмани босинг",
        ),
        quick_no=True,
    ),
    dict(
        key="ilmiy_unvon",
        label=("Ilmiy unvoni", "Илмий унвони"),
        prompt=(
            "Ilmiy unvoningiz bormi? Bo'lsa ayting, bo'lmasa pastdagi tugmani bosing",
            "Илмий унвонингиз борми? Бўлса айтинг, бўлмаса пастдаги тугмани босинг",
        ),
        quick_no=True,
    ),
    dict(
        key="chet_til",
        label=("Qaysi chet tillarini biladi", "Қайси чет тилларини билади"),
        prompt=(
            "Qaysi chet tillarini bilasiz va qay darajada? (masalan: Ingliz tili B2)",
            "Қайси чет тилларини биласиз ва қай даражада? (масалан: Инглиз тили B2)",
        ),
        quick_no=False,
    ),
    dict(
        key="mukofot",
        label=("Davlat mukofotlari bilan taqdirlanganmi", "Давлат мукофотлари билан тақдирланганми"),
        prompt=(
            "Davlat mukofotlari bilan taqdirlanganmisiz? Bo'lsa ayting, bo'lmasa pastdagi tugmani bosing",
            "Давлат мукофотлари билан тақдирлангансизми? Бўлса айтинг, бўлмаса пастдаги тугмани босинг",
        ),
        quick_no=True,
    ),
    dict(
        key="deputat",
        label=(
            "Xalq deputatlari yoki boshqa saylanadigan organlarning a'zosimi",
            "Халқ депутатлари ёки бошқа сайланадиган органларнинг аъзосими",
        ),
        prompt=(
            "Xalq deputatlari kengashi yoki boshqa saylanadigan organ a'zosimisiz? "
            "Bo'lsa ayting, bo'lmasa pastdagi tugmani bosing",
            "Халқ депутатлари кенгаши ёки бошқа сайланадиган орган аъзосимисиз? "
            "Бўлса айтинг, бўлмаса пастдаги тугмани босинг",
        ),
        quick_no=True,
    ),
]

QUICK_NO_TEXT = {L: "yo'q", C: "йўқ"}

# ---------------------------------------------------------------------------
# Mehnat faoliyati (ta'lim/ish tajribasi)
# ---------------------------------------------------------------------------
MEHNAT_HEADING = {L: "MEHNAT FAOLIYATI", C: "МЕҲНАТ ФАОЛИЯТИ"}
MEHNAT_INTRO = {
    L: "Endi mehnat (ish/o'qish) faoliyatingiz haqida so'rayman.",
    C: "Энди меҳнат (иш/ўқиш) фаолиятингиз ҳақида сўрайман.",
}
MEHNAT_FROM_PROMPT = {
    L: "Qachondan boshlab ishlagan/o'qigansiz? (yilni ayting, masalan: 2022)",
    C: "Қачондан бошлаб ишлаган/ўқигансиз? (йилни айтинг, масалан: 2022)",
}
MEHNAT_TO_PROMPT = {
    L: "Qachongacha? (yilni ayting; agar hozir ham davom etsa — \"hozirgacha\" deng)",
    C: "Қачонгача? (йилни айтинг; агар ҳозир ҳам давом этса — \"ҳозиргача\" денг)",
}
MEHNAT_PLACE_PROMPT = {
    L: "Qayerda va kim bo'lib ishlagansiz/o'qigansiz? (muassasa nomi va lavozim/mansab)",
    C: "Қаерда ва ким бўлиб ишлагансиз/ўқигансиз? (муассаса номи ва лавозим/мансаб)",
}
MEHNAT_ADD_MORE_PROMPT = {
    L: "Yana bitta ish/o'qish bosqichini qo'shasizmi?",
    C: "Яна битта иш/ўқиш босқичини қўшасизми?",
}

# ---------------------------------------------------------------------------
# Yaqin qarindoshlar
# ---------------------------------------------------------------------------
RELATIVES_HEADING = {
    L: "yaqin qarindoshlari haqida\nMA'LUMOT",
    C: "яқин қариндошлари ҳақида\nМАЪЛУМОТ",
}
RELATIVES_INTRO = {
    L: "Endi yaqin qarindoshlaringiz haqida so'rayman.",
    C: "Энди яқин қариндошларингиз ҳақида сўрайман.",
}
TABLE_HEADERS = {
    L: ["Qarindoshligi", "Familiyasi va ismi", "Tug'ilgan yili va joyi",
        "Ish joyi va lavozimi", "Turar joyi"],
    C: ["Қариндошлиги", "Фамилияси ва исми", "Туғилган йили ва жойи",
        "Иш жойи ва лавозими", "Турар жойи"],
}

REL_FIELD_PROMPTS = {
    "fio": {
        L: "{label}ning familiyasi va ismini ayting",
        C: "{label}нинг фамилияси ва исмини айтинг",
    },
    "tug": {
        L: "{label}ning tug'ilgan yili va joyini ayting",
        C: "{label}нинг туғилган йили ва жойини айтинг",
    },
    "ish": {
        L: "{label} qayerda ishlaydi/o'qiydi va lavozimi/mashg'uloti qanday? "
           "(masalan: nafaqada, uy bekasi, talaba va h.k. ham bo'lishi mumkin)",
        C: "{label} қаерда ишлайди/ўқийди ва лавозими/машғулоти қандай? "
           "(масалан: нафақада, уй бекаси, талаба ва ҳ.к. ҳам бўлиши мумкин)",
    },
    "turar": {
        L: "{label}ning turar joyi (manzili)ni ayting",
        C: "{label}нинг турар жойи (манзили)ни айтинг",
    },
}

# Har bir toifa: key, label(lat,cyr) — "kimning" shaklida ishlatiladi,
# gated -> avval "bormi?" so'raladi, multi -> "yana bormi?" bilan takrorlanadi,
# requires_spouse -> turmush o'rtog'i "bor" bo'lgandagina so'raladi,
# is_spouse_gate -> javobi has_spouse flagini belgilaydi,
# ask_gender -> avval qizi/o'g'li so'raladi va shu label dinamik bo'ladi.
RELATIVE_PLAN = [
    dict(key="ota", label=("Otangiz", "Отангиз"), col=("Otasi", "Отаси"),
         gated=False, multi=False),
    dict(key="ona", label=("Onangiz", "Онангиз"), col=("Onasi", "Онаси"),
         gated=False, multi=False),
    dict(key="aka", label=("Akangiz", "Акангиз"), col=("Akasi", "Акаси"),
         gated=True, multi=True),
    dict(key="uka", label=("Ukangiz", "Укангиз"), col=("Ukasi", "Укаси"),
         gated=True, multi=True),
    dict(key="opa", label=("Opangiz", "Опангиз"), col=("Opasi", "Опаси"),
         gated=True, multi=True),
    dict(key="singil", label=("Singlingiz", "Синглингиз"), col=("Singlisi", "Синглиси"),
         gated=True, multi=True),
    dict(key="spouse", label=("Turmush o'rtog'ingiz", "Турмуш ўртоғингиз"),
         col=("Turmush o'rtog'i", "Турмуш ўртоғи"),
         gated=True, multi=False, is_spouse_gate=True),
    dict(key="farzand", label=("Farzandingiz", "Фарзандингиз"), col=None,
         gated=True, multi=True, requires_spouse=True, ask_gender=True),
    dict(key="qaynona", label=("Qaynonangiz", "Қайнонангиз"), col=("Qaynonasi", "Қайнонаси"),
         gated=True, multi=False, requires_spouse=True),
    dict(key="qaynota", label=("Qaynotangiz", "Қайнотангиз"), col=("Qaynotasi", "Қайнотаси"),
         gated=True, multi=False, requires_spouse=True),
]

PRESENCE_PROMPT = {
    L: "{label} bormi?",
    C: "{label} борми?",
}

FAMILY_GATE_PROMPT = {
    L: "Ota-onangiz, aka-uka, opa-singillaringiz sizlar bilan bitta manzilda "
       "(turar joyda) yashaydimi?",
    C: "Ота-онангиз, ака-ука, опа-сингилларингиз сизлар билан битта манзилда "
       "(турар жойда) яшайдими?",
}
SPOUSE_GATE_PROMPT = {
    L: "Turmush o'rtog'ingiz va farzandlaringiz siz bilan bitta manzilda yashaydimi?",
    C: "Турмуш ўртоғингиз ва фарзандларингиз сиз билан битта манзилда яшайдими?",
}
SHARED_ADDRESS_ASK = {
    L: "Manzilni ayting (bu manzil tegishli barcha qarindoshlar uchun avtomatik ishlatiladi):",
    C: "Манзилни айтинг (бу манзил тегишли барча қариндошлар учун автоматик ишлатилади):",
}

GENDER_PROMPT = {
    L: "Farzandingiz qiz bolami yoki o'g'il bolami?",
    C: "Фарзандингиз қиз болами ёки ўғил болами?",
}
GENDER_LABELS = {
    "qiz": {L: "Qizi", C: "Қизи"},
    "ogil": {L: "O'g'li", C: "Ўғли"},
}

# ---------------------------------------------------------------------------
# Tugma matnlari
# ---------------------------------------------------------------------------
BTN_CONFIRM = {L: "✅ Tasdiqlash", C: "✅ Тасдиқлаш"}
BTN_EDIT = {L: "✏️ Qayta yozish", C: "✏️ Қайта ёзиш"}
BTN_COPY = {L: "📋 Nusxalab, tuzatish", C: "📋 Нусхалаб, тузатиш"}
BTN_QUICK_NO = {L: "❌ Yo'q", C: "❌ Йўқ"}
BTN_YES = {L: "✅ Bor", C: "✅ Бор"}
BTN_NO = {L: "❌ Yo'q", C: "❌ Йўқ"}
BTN_ADD_MORE = {L: "➕ Ha, qo'shaman", C: "➕ Ҳа, қўшаман"}
BTN_NO_MORE = {L: "➡️ Yo'q, davom etamiz", C: "➡️ Йўқ, давом этамиз"}
BTN_GENDER_QIZ = {L: "👧 Qizi", C: "👧 Қизи"}
BTN_GENDER_OGIL = {L: "👦 O'g'li", C: "👦 Ўғли"}

ASK_VOICE_HINT = {
    L: "\n\n🎤 Ovozli xabar yuboring.",
    C: "\n\n🎤 Овозли хабар юборинг.",
}
EDIT_ASK_TEXT = {
    L: "Iltimos, to'g'ri variantni yozib yuboring (matn ko'rinishida):",
    C: "Илтимос, тўғри вариантни ёзиб юборинг (матн кўринишида):",
}
TRANSCRIBE_FAIL = {
    L: "Kechirasiz, ovozingizni tanib bo'lmadi. Yana urinib ko'ring yoki matn ko'rinishida yozib yuboring.",
    C: "Кечирасиз, овозингизни таниб бўлмади. Яна уриниб кўринг ёки матн кўринишида ёзиб юборинг.",
}
CONFIRM_PREVIEW = {
    L: "Shunday tushundim:\n\n«{text}»\n\nTo'g'rimi?",
    C: "Шундай тушундим:\n\n«{text}»\n\nТўғрими?",
}
PHOTO_PROMPT = {
    L: "Deyarli tayyor! 📸 Endi 3x4 (yoki istalgan) rasmingizni surat (photo) "
       "sifatida yuboring — men uni hujjatga joylashtirib beraman.",
    C: "Деярли тайёр! 📸 Энди 3x4 (ёки истаган) расмингизни сурат (photo) "
       "сифатида юборинг — мен уни ҳужжатга жойлаштириб бераман.",
}
PHOTO_WAIT_HINT = {
    L: "Iltimos, rasmni 'photo' (surat) sifatida yuboring, fayl sifatida emas.",
    C: "Илтимос, расмни 'photo' (сурат) сифатида юборинг, файл сифатида эмас.",
}
GENERATING = {
    L: "Rahmat! Hujjat tayyorlanmoqda... ⏳",
    C: "Раҳмат! Ҳужжат тайёрланмоқда... ⏳",
}
DONE_MSG = {
    L: "✅ Ob'ektivkangiz tayyor! Qayta boshlash uchun /start buyrug'ini yuboring.",
    C: "✅ Объективкангиз тайёр! Қайта бошлаш учун /start буйруғини юборинг.",
}
DOC_ERROR_MSG = {
    L: "❌ Kechirasiz, hujjatni tayyorlashda xatolik yuz berdi (ehtimol rasm "
       "buzilgan yoki internet uzilib qolgan). Iltimos, rasmni qaytadan yuboring.",
    C: "❌ Кечирасиз, ҳужжатни тайёрлашда хатолик юз берди (эҳтимол расм "
       "бузилган ёки интернет узилиб қолган). Илтимос, расмни қайтадан юборинг.",
}
GENERIC_ERROR_MSG = {
    L: "❌ Kutilmagan xatolik yuz berdi. Iltimos, /start bilan qaytadan boshlang.",
    C: "❌ Кутилмаган хатолик юз берди. Илтимос, /start билан қайтадан бошланг.",
}
SESSION_LOST_MSG = {
    L: "⚠️ Kechirasiz, sessiya (suhbat holati) uzilib qoldi — server internet "
       "yoki qayta ishga tushish sababli ma'lumotlaringizni yo'qotib qo'ydi. "
       "Iltimos, /start bilan qaytadan boshlang.",
    C: "⚠️ Кечирасиз, сессия (суҳбат ҳолати) узилиб қолди — сервер интернет "
       "ёки қайта ишга тушиш сабабли маълумотларингизни йўқотиб қўйди. "
       "Илтимос, /start билан қайтадан бошланг.",
}
NOT_STARTED_MSG = {
    L: "Boshlash uchun /start buyrug'ini yuboring.",
    C: "Бошлаш учун /start буйруғини юборинг.",
}
START_PROMPT = "Assalomu alaykum! Men sizga ob'ektivka (МАЪЛУМОТНОМА) tayyorlashda yordam beraman.\nQaysi tilda ish olib boramiz?"
NOT_VOICE_OR_TEXT = {
    L: "Iltimos, ovozli xabar yuboring (yoki matn yozing).",
    C: "Илтимос, овозли хабар юборинг (ёки матн ёзинг).",
}
