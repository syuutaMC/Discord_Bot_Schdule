#!/usr/bin/env python3.10
import discord
import os

from dao_sqlite3 import dao_sqlite3


# if you change constants, also update docker-compose
TOKEN = os.getenv("TOKEN")


intents = discord.Intents.default()
intents.members = True
intents.guild_scheduled_events = True
client = discord.Client(intents=intents)

db = dao_sqlite3()


# 起動時に動作する処理
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('Version : 0.1')

# イベント作成時
@client.event
async def on_scheduled_event_create(event):
    guild = event.guild
    ## イベント作成時にロール作成とチャンネルを作成する
    role = await guild.create_role(name = f'{event.start_time.strftime('%Y-%m-%d')}')

    member = guild.get_member(event.creator_id)
    await member.add_roles(role)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        role: discord.PermissionOverwrite(view_channel=True)
    }

    channel = await guild.create_text_channel(f'{event.start_time.strftime('%Y-%m-%d')}_飲み会', overwrites=overwrites)
    print(event.id, role.id)

    db.insert_event(event.id, role.id, channel.id)

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
    role = guild.get_role(role_id)
    await member.add_roles(role)


@client.event
async def on_scheduled_event_user_remove(event, user):
    role_id = db.get_role_id(event.id)

    print(role_id)

    # ロールを付与する
    guild = event.guild
    member = guild.get_member(user.id)
    role = guild.get_role(role_id)
    await member.remove_roles(role)

@client.event
async def on_scheduled_event_update(before, after):

    if before.start_time != after.start_time:
        channel_id = db.get_channel_id(after.id)
        role_id = db.get_role_id(after.id)

        guild = after.guild
        text_channel = guild.get_channel(channel_id)
        role = guild.get_role(role_id)

        await text_channel.edit(name = f'{after.start_time.strftime('%Y-%m-%d')}_飲み会')
        await role.edit(name = f'{after.start_time.strftime('%Y-%m-%d')}')


if __name__ == '__main__':
    client.run(TOKEN)
