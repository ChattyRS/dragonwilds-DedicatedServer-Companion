# Dragonwilds Dedicated Server Companion

A lightweight companion API for RuneScape: Dragonwilds Dedicated Servers.

Forked from [xdrushxd/dragonwilds-DedicatedServer-Companion](https://github.com/xdrushxd/dragonwilds-DedicatedServer-Companion).

Removed docker requirement and using PostgreSQL instead of MySQL. 

Some parts of the original may be non-functional. I am only using the API to tell whether the server is online, how many players are active, and when the last save was.

## API Output

```json
{
  "status": "online",
  "server": "Dragonwilds",
  "players_online": 1,
  "max_players": 6,
  "players_text": "xdrushxd",
  "uptime": "16h 15m",
  "last_save": "4m ago",
  "memory": "1.7GiB",
  "cpu": "6.5%"
}
```

## Requirements

- RuneScape: Dragonwilds dedicated server
- Python 3
- Flask
- psutil
- sqlalchemy
- psycopg2