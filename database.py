"""
Barcha statistikani (kim nechta xabar yozgan, nechta odam qo'shgan,
nechta ogohlantirish olgan) saqlab boruvchi oddiy SQLite ombori.

Kelajakda yangi qoida qo'shmoqchi bo'lsangiz, shu yerga yangi jadval/funksiya
qo'shishingiz mumkin - qolgan kod bilan aralashib ketmaydi.
"""

import sqlite3
import datetime
import threading

DB_PATH = "group_bot.db"
_lock = threading.Lock()


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            invite_count INTEGER NOT NULL DEFAULT 0,
            warnings INTEGER NOT NULL DEFAULT 0,
            paid_bonus INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Eski (yangilanishdan oldingi) bazalarda paid_bonus ustuni bo'lmasligi mumkin -
    # xavfsiz tarzda qo'shib qo'yamiz.
    try:
        cur.execute("ALTER TABLE users ADD COLUMN paid_bonus INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            user_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            message_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (user_id, day)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invite_links (
            link TEXT PRIMARY KEY,
            owner_id INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pending_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            photo_file_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS staged_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            text TEXT,
            photo_file_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _today():
    return datetime.date.today().isoformat()


def ensure_user(user_id, username=None):
    with _lock:
        conn = get_conn()
        conn.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username",
            (user_id, username),
        )
        conn.commit()
        conn.close()


def increment_message_count(user_id):
    day = _today()
    with _lock:
        conn = get_conn()
        conn.execute(
            "INSERT INTO daily_stats (user_id, day, message_count) VALUES (?, ?, 1) "
            "ON CONFLICT(user_id, day) DO UPDATE SET message_count = message_count + 1",
            (user_id, day),
        )
        conn.commit()
        row = conn.execute(
            "SELECT message_count FROM daily_stats WHERE user_id=? AND day=?",
            (user_id, day),
        ).fetchone()
        conn.close()
        return row["message_count"] if row else 1


def get_message_count(user_id):
    day = _today()
    conn = get_conn()
    row = conn.execute(
        "SELECT message_count FROM daily_stats WHERE user_id=? AND day=?",
        (user_id, day),
    ).fetchone()
    conn.close()
    return row["message_count"] if row else 0


def get_invite_count(user_id):
    conn = get_conn()
    row = conn.execute("SELECT invite_count FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row["invite_count"] if row else 0


def add_invite(owner_id):
    with _lock:
        conn = get_conn()
        conn.execute(
            "UPDATE users SET invite_count = invite_count + 1 WHERE user_id=?",
            (owner_id,),
        )
        conn.commit()
        conn.close()


def add_warning(user_id):
    with _lock:
        conn = get_conn()
        conn.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id=?", (user_id,))
        conn.commit()
        row = conn.execute("SELECT warnings FROM users WHERE user_id=?", (user_id,)).fetchone()
        conn.close()
        return row["warnings"] if row else 0


def reset_warnings(user_id):
    with _lock:
        conn = get_conn()
        conn.execute("UPDATE users SET warnings = 0 WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()


def save_invite_link(link, owner_id):
    with _lock:
        conn = get_conn()
        conn.execute(
            "INSERT INTO invite_links (link, owner_id) VALUES (?, ?) "
            "ON CONFLICT(link) DO UPDATE SET owner_id=excluded.owner_id",
            (link, owner_id),
        )
        conn.commit()
        conn.close()


def get_owner_by_link(link):
    conn = get_conn()
    row = conn.execute("SELECT owner_id FROM invite_links WHERE link=?", (link,)).fetchone()
    conn.close()
    return row["owner_id"] if row else None


def get_link_by_owner(owner_id):
    conn = get_conn()
    row = conn.execute(
        "SELECT link FROM invite_links WHERE owner_id=? ORDER BY rowid DESC LIMIT 1",
        (owner_id,),
    ).fetchone()
    conn.close()
    return row["link"] if row else None


def top_inviters(limit=10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT user_id, username, invite_count FROM users "
        "WHERE invite_count > 0 ORDER BY invite_count DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def get_paid_bonus(user_id):
    conn = get_conn()
    row = conn.execute("SELECT paid_bonus FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row["paid_bonus"] if row else 0


def add_paid_bonus(user_id, amount):
    with _lock:
        conn = get_conn()
        conn.execute(
            "UPDATE users SET paid_bonus = paid_bonus + ? WHERE user_id=?",
            (amount, user_id),
        )
        conn.commit()
        conn.close()


def create_pending_payment(user_id, username, photo_file_id):
    with _lock:
        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO pending_payments (user_id, username, photo_file_id, status, created_at) "
            "VALUES (?, ?, ?, 'pending', ?)",
            (user_id, username, photo_file_id, datetime.datetime.now().isoformat()),
        )
        conn.commit()
        payment_id = cur.lastrowid
        conn.close()
        return payment_id


def get_payment(payment_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM pending_payments WHERE id=?", (payment_id,)).fetchone()
    conn.close()
    return row


def set_payment_status(payment_id, status):
    """Holatni yangilaydi, lekin faqat u hali 'pending' bo'lsa (ikki marta bosilib
    ketmasligi uchun). Muvaffaqiyatli yangilansa True qaytaradi."""
    with _lock:
        conn = get_conn()
        cur = conn.execute(
            "UPDATE pending_payments SET status=? WHERE id=? AND status='pending'",
            (status, payment_id),
        )
        conn.commit()
        changed = cur.rowcount > 0
        conn.close()
        return changed


def create_staged_post(admin_id, text, photo_file_id):
    with _lock:
        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO staged_posts (admin_id, text, photo_file_id, status, created_at) "
            "VALUES (?, ?, ?, 'pending', ?)",
            (admin_id, text, photo_file_id, datetime.datetime.now().isoformat()),
        )
        conn.commit()
        staged_id = cur.lastrowid
        conn.close()
        return staged_id


def get_staged_post(staged_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM staged_posts WHERE id=?", (staged_id,)).fetchone()
    conn.close()
    return row


def set_staged_status(staged_id, status):
    """Faqat hali 'pending' bo'lgan yozuvni yangilaydi (ikki marta bosilib
    ketmasligi uchun). Muvaffaqiyatli bo'lsa True qaytaradi."""
    with _lock:
        conn = get_conn()
        cur = conn.execute(
            "UPDATE staged_posts SET status=? WHERE id=? AND status='pending'",
            (status, staged_id),
        )
        conn.commit()
        changed = cur.rowcount > 0
        conn.close()
        return changed


def top_writers_today(limit=10):
    day = _today()
    conn = get_conn()
    rows = conn.execute(
        "SELECT d.user_id, u.username, d.message_count FROM daily_stats d "
        "LEFT JOIN users u ON u.user_id = d.user_id "
        "WHERE d.day=? ORDER BY d.message_count DESC LIMIT ?",
        (day, limit),
    ).fetchall()
    conn.close()
    return rows
