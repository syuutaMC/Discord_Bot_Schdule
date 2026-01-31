from __future__ import annotations

import datetime


def log_command(command_name: str, guild_id: int | None, user_id: int | None) -> None:
    timestamp = datetime.datetime.utcnow().isoformat(timespec='seconds')
    print(f"[cmd] {timestamp} name={command_name} guild={guild_id} user={user_id}")
