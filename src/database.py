import os
import pymysql
from datetime import datetime
from src.configuration import config

MYSQL_HOST = config['SQL_HOST']
MYSQL_PORT = config['SQL_PORT']
MYSQL_DATABASE = config['SQL_DATABASE']
MYSQL_USER = config['SQL_USER']
MYSQL_PASSWORD = config['SQL_PASSWORD']


def db_enabled():
    return all([MYSQL_HOST, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD])


def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


def init_db():
    if not db_enabled():
        print("Database disabled: missing MySQL environment variables")
        return

    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
        IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'player_sessions')
        BEGIN
            CREATE TABLE player_sessions (
                id BIGSERIAL PRIMARY KEY,
                player_name VARCHAR(100) NOT NULL,
                account_id VARCHAR(100) NOT NULL,
                joined_at TIMESTAMP NOT NULL,
                left_at TIMESTAMP NULL,
                duration_seconds INT DEFAULT 0
            );
            CREATE INDEX idx_player_sessions_player_name ON player_sessions (player_name);
            CREATE INDEX idx_player_sessions_account_id ON player_sessions (account_id);
            CREATE INDEX idx_player_sessions_joined_at ON player_sessions (joined_at);
        END
        """)

        cur.execute("""
        IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'server_metrics')
        BEGIN
            CREATE TABLE server_metrics (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                cpu_percent FLOAT NULL,
                memory_gib FLOAT NULL,
                players_online INT NOT NULL
            );
            CREATE INDEX idx_server_metrics_timestamp ON server_metrics (timestamp);
        END
        """)

        cur.execute("""
        IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'events')
        BEGIN
            CREATE TABLE events (
                id BIGSERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                message VARCHAR(255) NOT NULL
            );
            CREATE INDEX idx_events_timestamp ON events (timestamp);
        END
        """)

    conn.close()
    print("Database initialized")


def log_event(message):
    if not db_enabled():
        return

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO events (timestamp, message) VALUES (%s, %s)",
            (datetime.now(), message)
        )
    conn.close()


def player_join(account_id, player_name):
    if not db_enabled():
        return

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO player_sessions (player_name, account_id, joined_at)
            VALUES (%s, %s, %s)
        """, (player_name, account_id, datetime.now()))
    conn.close()


def player_leave(account_id):
    if not db_enabled():
        return

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, joined_at
            FROM player_sessions
            WHERE account_id = %s AND left_at IS NULL
            ORDER BY joined_at DESC
            LIMIT 1
        """, (account_id,))
        session = cur.fetchone()

        if session:
            duration = int((datetime.now() - session["joined_at"]).total_seconds())
            cur.execute("""
                UPDATE player_sessions
                SET left_at = %s, duration_seconds = %s
                WHERE id = %s
            """, (datetime.now(), duration, session["id"]))

    conn.close()


def log_metrics(cpu_percent, memory_gib, players_online):
    if not db_enabled():
        return

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO server_metrics
            (timestamp, cpu_percent, memory_gib, players_online)
            VALUES (%s, %s, %s, %s)
        """, (datetime.now(), cpu_percent, memory_gib, players_online))
    conn.close()

from utils import seconds_to_human


def get_leaderboard(limit=10):
    if not db_enabled():
        return []

    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                player_name,
                COUNT(*) AS sessions,
                SUM(duration_seconds) AS total_seconds,
                MAX(duration_seconds) AS longest_session
            FROM player_sessions
            WHERE duration_seconds > 0
            GROUP BY player_name
            ORDER BY total_seconds DESC
            LIMIT %s
        """, (limit,))

        rows = cur.fetchall()

    conn.close()

    leaderboard = []

    for row in rows:
        total = row["total_seconds"] or 0
        longest = row["longest_session"] or 0

        leaderboard.append({
            "player": row["player_name"],
            "sessions": row["sessions"],
            "total_seconds": int(total),
            "playtime": seconds_to_human(total),
            "longest_session": seconds_to_human(longest)
        })

    return leaderboard