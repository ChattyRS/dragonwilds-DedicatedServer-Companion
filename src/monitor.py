import psutil
import re
import threading
import time
import os
from src.configuration import config
from src.state import set_player, remove_player, update_field, add_event, clear_players
from src.database import log_event, player_join, player_leave


def server_running():
    process_name = config['PROCESS_NAME']

    for proc in psutil.process_iter(['name']):
        try:
            # Compare process name case-insensitively
            if proc.info['name'].lower() == process_name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    return False


def parse_line(line):
    added = re.search(r"Player ADDED to session \[(.*?)\]-\[(.*?)\]", line)
    if added:
        account = added.group(1)
        name = added.group(2)

        set_player(account, name)
        player_join(account, name)
        log_event(f"{name} joined")
        return

    removed = re.search(r"Player Removed from session \[(.*?)\]-\[(.*?)\]", line)
    if removed:
        account = removed.group(1)
        name = removed.group(2)

        remove_player(account, name)
        player_leave(account)
        log_event(f"{name} left")
        return

    world = re.search(r"Save completed SUCCESSFULLY \(slot:\s*(.*?)\)", line)
    if world:
        update_field("world", world.group(1))
        return

    version_patterns = [
        r"version[:= ]+([0-9A-Za-z\.\-_]+)",
        r"build[:= ]+([0-9A-Za-z\.\-_]+)",
        r"server version[:= ]+([0-9A-Za-z\.\-_]+)"
    ]

    for pattern in version_patterns:
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            update_field("version", match.group(1))
            return
        

def follow_logs_forever():
    was_running = False

    def log_stopped():
        clear_players()
        add_event("Server stopped")
        log_event("Server stopped")
        update_field("status", "offline")

    log_file = config['LOG_FILE_PATH']
    while True:
        if not server_running():
            print(f"[!] Server not running. Retrying in 5 seconds...")
            if was_running:
                log_stopped()
                was_running = False
            time.sleep(5)
            continue
        if not os.path.exists(log_file):
            print(f"[!] Log file not found. Retrying in 5 seconds...")
            if was_running:
                log_stopped()
                was_running = False
            time.sleep(5)
            continue

        if not was_running:
            clear_players()
            add_event("Server started")
            log_event("Server started")
            update_field("status", "online")
            was_running = True

        # Open file with 'errors="ignore"' to safely handle Windows encoding issues
        with open(log_file, "r", errors="ignore", encoding="utf-8") as f:
            # 1. First boot: Parse existing log content to catch current state/version
            # print("[*] Parsing initial log history...")
            # for line in f:
            #     parse_line(line)
                
            # 2. Move to the end of the file and stream new entries live
            f.seek(0, os.SEEK_END)
            print("[*] Monitoring logs for real-time updates...")
            
            while True:
                time.sleep(1)
                if not server_running():
                    print(f"[!] Server not running. Retrying in 5 seconds...")
                    log_stopped()
                    was_running = False
                    time.sleep(5)
                    break
                lines = f.readlines()
                if not lines or len(lines) == 0:
                    # No new logs yet; wait briefly to prevent high CPU usage
                    time.sleep(1)
                    # Check if file was rotated or cleared by the server engine
                    if os.path.exists(log_file) and f.tell() > os.path.getsize(log_file):
                        print("[*] Log file appears to have been rotated. Resetting tracker...")
                        clear_players()
                        add_event("Log stream reconnecting")
                        time.sleep(5)
                        break
                    continue
                for line in lines:
                    parse_line(line)


def start_monitor():
    thread = threading.Thread(target=follow_logs_forever, daemon=True)
    thread.start()