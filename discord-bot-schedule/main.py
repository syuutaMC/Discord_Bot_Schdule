#!/usr/bin/env python3.10
import discord
import os

from discord import app_commands

from commands import setup_schedule_commands

from dao_sqlite3 import dao_sqlite3


# if you change constants, also update docker-compose
ENV = os.getenv("ENV", "prod")


def _get_env_int(name: str, default: int = 0) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


if ENV == "test":
    TOKEN = os.getenv("TOKEN_TEST")
    UPCOMING_CATEGORY_ID = _get_env_int("UPCOMING_CATEGORY_ID_TEST")
    ENDED_CATEGORY_ID = _get_env_int("ENDED_CATEGORY_ID_TEST")
    TARGET_GUILD_ID = _get_env_int("GUILD_ID_TEST")
else:
    TOKEN = os.getenv("TOKEN")
    UPCOMING_CATEGORY_ID = _get_env_int("UPCOMING_CATEGORY_ID")
    ENDED_CATEGORY_ID = _get_env_int("ENDED_CATEGORY_ID")
    TARGET_GUILD_ID = _get_env_int("GUILD_ID")


intents = discord.Intents.default()
intents.members = True
intents.guild_scheduled_events = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

db = dao_sqlite3()
setup_schedule_commands(tree, db, UPCOMING_CATEGORY_ID, ENDED_CATEGORY_ID)


# 起動時に動作する処理
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('Version : 0.1')
    await _resync_event_members()
    await tree.sync()


async def _resync_event_members():
    if TARGET_GUILD_ID:
        guilds = [client.get_guild(TARGET_GUILD_ID)]
    else:
        guilds = client.guilds

    for guild in guilds:
        if not guild:
            continue
        try:
            events = await guild.fetch_scheduled_events()
        except discord.HTTPException:
            continue

        for event in events:
            if event.status != discord.EventStatus.scheduled:
                continue
            role_id = db.get_role_id(event.id)
            role = guild.get_role(role_id) if role_id else None
            if not role:
                role = await guild.create_role(name=f"{event.start_time.strftime('%Y-%m-%d')}")

            channel_id = db.get_channel_id(event.id)
            channel = guild.get_channel(channel_id) if channel_id else None
            if not channel:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    role: discord.PermissionOverwrite(view_channel=True),
                }
                upcoming_category = guild.get_channel(UPCOMING_CATEGORY_ID)
                channel = await guild.create_text_channel(
                    f"{event.start_time.strftime('%Y-%m-%d')}_飲み会",
                    overwrites=overwrites,
                    category=upcoming_category,
                )

            if not role_id or not channel_id:
                db.insert_event(event.id, channel.id, role.id)

            try:
                async for attendee in event.users(with_members=True):
                    member = None
                    if isinstance(attendee, discord.Member):
                        member = attendee
                    elif isinstance(attendee, discord.User):
                        member = guild.get_member(attendee.id)
                    if member and role not in member.roles:
                        await member.add_roles(role)
            except discord.HTTPException as e:
                print(f"Error fetching users for event {event.id}: {e}")
                continue

# イベント作成時
@client.event
async def on_scheduled_event_create(event):
    guild = event.guild
    ## イベント作成時にロール作成とチャンネルを作成する
    role = await guild.create_role(name = f"{event.start_time.strftime('%Y-%m-%d')}")

    member = guild.get_member(event.creator_id)
    await member.add_roles(role)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        role: discord.PermissionOverwrite(view_channel=True)
    }

    upcoming_category = guild.get_channel(UPCOMING_CATEGORY_ID)
    channel = await guild.create_text_channel(
        f"{event.start_time.strftime('%Y-%m-%d')}_飲み会",
        overwrites=overwrites,
        category=upcoming_category,
    )
    print(event.id, role.id)

    db.insert_event(event.id, channel.id, role.id)

@client.event
async def on_scheduled_event_delete(event):
    print("delete")
    pass


@client.event
async def on_scheduled_event_user_add(event, user):
    role_id = db.get_role_id(event.id)

    print(role_id)
    # ロールを付与する
    guild = event.guild
    member = guild.get_member(user.id)
    role = guild.get_role(role_id) if role_id else None
    if role:
        await member.add_roles(role)


@client.event
async def on_scheduled_event_user_remove(event, user):
    role_id = db.get_role_id(event.id)

    print(role_id)

    # ロールを付与する
    guild = event.guild
    member = guild.get_member(user.id)
    role = guild.get_role(role_id) if role_id else None
    if role:
        await member.remove_roles(role)

@client.event
async def on_scheduled_event_update(before, after):

    if before.start_time != after.start_time:
        channel_id = db.get_channel_id(after.id)
        role_id = db.get_role_id(after.id)

        guild = after.guild
        text_channel = guild.get_channel(channel_id)
        role = guild.get_role(role_id)

        if text_channel:
            await text_channel.edit(name = f"{after.start_time.strftime('%Y-%m-%d')}_飲み会")
        if role:
            await role.edit(name = f"{after.start_time.strftime('%Y-%m-%d')}")

    if before.status != after.status:
        channel_id = db.get_channel_id(after.id)
        if not channel_id:
            return
        guild = after.guild
        text_channel = guild.get_channel(channel_id)
        if not text_channel:
            return

        if after.status == discord.EventStatus.completed:
            ended_category = guild.get_channel(ENDED_CATEGORY_ID)
            await text_channel.edit(category=ended_category)


if __name__ == '__main__':
    client.run(TOKEN)
