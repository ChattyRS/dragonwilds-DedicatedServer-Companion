from sqlalchemy import create_engine, text
from datetime import datetime
from src.configuration import config
from src.utils import seconds_to_human

SQL_HOST = config['SQL_HOST']
SQL_PORT = config['SQL_PORT']
SQL_DATABASE = config['SQL_DATABASE']
SQL_USER = config['SQL_USER']
SQL_PASSWORD = config['SQL_PASSWORD']


def db_enabled():
    return all([SQL_HOST, SQL_DATABASE, SQL_USER, SQL_PASSWORD])


def get_connection_engine():
    # Create the connection engine (using the psycopg2 synchronous driver)
    DATABASE_URL = f"postgresql+psycopg2://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}/{SQL_DATABASE}"
    engine = create_engine(DATABASE_URL, echo=True)  # echo=True logs the raw SQL statements to the console
    return engine


def init_db():
    if not db_enabled():
        print("Database disabled: missing MySQL environment variables")
        return

    with get_connection_engine().connect() as connection:
        connection.execute(text("""
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
        """))
        connection.commit()

        connection.execute(text("""
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
        """))
        connection.commit()

        connection.execute(text("""
            IF NOT EXISTS (SELECT * FROM information_schema.tables WHERE table_name = 'events')
            BEGIN
                CREATE TABLE events (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    message VARCHAR(255) NOT NULL
                );
                CREATE INDEX idx_events_timestamp ON events (timestamp);
            END
        """))
        connection.commit()

    print("Database initialized")


def log_event(message):
    if not db_enabled():
        return

    with get_connection_engine().connect() as connection:
        connection.execute(
            text("INSERT INTO events (timestamp, message) VALUES (:timestamp, :message)"),
            { "timestamp": datetime.now(), "message": message }
        )
        connection.commit()


def player_join(account_id, player_name):
    if not db_enabled():
        return

    with get_connection_engine().connect() as connection:
        connection.execute(
            text("INSERT INTO player_sessions (player_name, account_id, joined_at) VALUES (:player_name, :account_id, :joined_at)"),
            { "player_name": player_name, "account_id": account_id, "joined_at": datetime.now() }
        )
        connection.commit()


def player_leave(account_id):
    if not db_enabled():
        return

    with get_connection_engine().connect() as connection:
        session = connection.execute(text("""
            SELECT id, joined_at
            FROM player_sessions
            WHERE account_id = :account_id AND left_at IS NULL
            ORDER BY joined_at DESC
            LIMIT 1
        """), { "account_id": account_id }
        ).first()
        connection.commit()

        if session:
            duration = int((datetime.now() - session["joined_at"]).total_seconds())
            connection.execute(text("""
                UPDATE player_sessions
                SET left_at = :left_at, duration_seconds = :duration
                WHERE id = :id
            """), { "left_at": datetime.now(), "duration": duration, "id": session["id"] }
            )
            connection.commit()


def get_leaderboard(limit=10):
    if not db_enabled():
        return []

    with get_connection_engine().connect() as connection:
        rows = connection.execute(text("""
            SELECT
                player_name,
                COUNT(*) AS sessions,
                SUM(duration_seconds) AS total_seconds,
                MAX(duration_seconds) AS longest_session
            FROM player_sessions
            WHERE duration_seconds > 0
            GROUP BY player_name
            ORDER BY total_seconds DESC
            LIMIT :limit
        """), { "limit": limit }
        ).all()
        connection.commit()

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