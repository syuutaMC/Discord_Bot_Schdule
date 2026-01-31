#!/usr/bin/env python3.10
import discord
import os

from discord import app_commands

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
else:
    TOKEN = os.getenv("TOKEN")
    UPCOMING_CATEGORY_ID = _get_env_int("UPCOMING_CATEGORY_ID")
    ENDED_CATEGORY_ID = _get_env_int("ENDED_CATEGORY_ID")


intents = discord.Intents.default()
intents.members = True
intents.guild_scheduled_events = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

db = dao_sqlite3()


# 起動時に動作する処理
@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('Version : 0.1')
    await tree.sync()

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


def _format_event_date(dt):
    return dt.strftime('%Y-%m-%d')


def _chunk_lines(lines, max_len=1900):
    chunks = []
    current = ''
    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            chunks.append(current)
            current = ''
        current += line + '\n'
    if current:
        chunks.append(current)
    return chunks


schedule_group = app_commands.Group(name='schedule', description='スケジュール管理コマンド')


@schedule_group.command(name='list', description='DBに保存されているスケジュール一覧を表示')
@app_commands.checks.has_permissions(manage_guild=True)
async def schedule_list(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message('サーバー内で実行してください。', ephemeral=True)
        return

    events = db.list_events()
    if not events:
        await interaction.response.send_message('登録済みスケジュールはありません。', ephemeral=True)
        return

    lines = ['event_id | status | channel | role']
    for event_id, channel_id, role_id in events:
        channel = interaction.guild.get_channel(channel_id)
        role = interaction.guild.get_role(role_id)
        channel_text = channel.mention if channel else str(channel_id)
        role_text = role.mention if role else str(role_id)

        status_text = '不明'
        try:
            scheduled_event = await interaction.guild.fetch_scheduled_event(event_id)
            if scheduled_event.status == discord.EventStatus.completed:
                status_text = '終了済み'
            elif scheduled_event.status == discord.EventStatus.scheduled:
                status_text = '開催前'
            elif scheduled_event.status == discord.EventStatus.active:
                status_text = '開催中'
            elif scheduled_event.status == discord.EventStatus.canceled:
                status_text = 'キャンセル'
        except discord.NotFound:
            status_text = '削除済み'
        except discord.HTTPException:
            status_text = '別サーバー/不明'

        lines.append(f'{event_id} | {status_text} | {channel_text} | {role_text}')

    chunks = _chunk_lines(lines)
    await interaction.response.send_message(chunks[0], ephemeral=True)
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk, ephemeral=True)


@schedule_group.command(name='info', description='指定したスケジュールの詳細を表示')
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(event_id='DiscordスケジュールイベントのID')
async def schedule_info(interaction: discord.Interaction, event_id: int):
    if not interaction.guild:
        await interaction.response.send_message('サーバー内で実行してください。', ephemeral=True)
        return

    record = db.get_event(event_id)
    if not record:
        await interaction.response.send_message('該当のレコードが見つかりません。', ephemeral=True)
        return

    _, channel_id, role_id = record
    channel = interaction.guild.get_channel(channel_id)
    role = interaction.guild.get_role(role_id)

    event_info = '未取得'
    try:
        scheduled_event = await interaction.guild.fetch_scheduled_event(event_id)
        event_info = f"{scheduled_event.name} / {scheduled_event.start_time}"
    except discord.NotFound:
        event_info = 'イベントが見つかりません'

    message = (
        f'event_id: {event_id}\n'
        f'event: {event_info}\n'
        f'channel: {channel.mention if channel else channel_id}\n'
        f'role: {role.mention if role else role_id}'
    )
    await interaction.response.send_message(message, ephemeral=True)


@schedule_group.command(name='delete', description='指定したスケジュールを削除（DB/チャンネル/ロール）')
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(event_id='DiscordスケジュールイベントのID')
async def schedule_delete(interaction: discord.Interaction, event_id: int):
    if not interaction.guild:
        await interaction.response.send_message('サーバー内で実行してください。', ephemeral=True)
        return

    record = db.get_event(event_id)
    if not record:
        await interaction.response.send_message('該当のレコードが見つかりません。', ephemeral=True)
        return

    _, channel_id, role_id = record
    channel = interaction.guild.get_channel(channel_id)
    role = interaction.guild.get_role(role_id)

    if channel:
        await channel.delete(reason='schedule delete command')
    if role:
        await role.delete(reason='schedule delete command')

    db.delete_event(event_id)
    await interaction.response.send_message('削除しました。', ephemeral=True)


@schedule_group.command(name='fix', description='不整合を検出して修復')
@app_commands.checks.has_permissions(manage_guild=True)
async def schedule_fix(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message('サーバー内で実行してください。', ephemeral=True)
        return

    records = db.list_events()
    if not records:
        await interaction.response.send_message('登録済みスケジュールはありません。', ephemeral=True)
        return

    fixed = 0
    cleaned = 0
    for event_id, channel_id, role_id in records:
        channel = interaction.guild.get_channel(channel_id)
        role = interaction.guild.get_role(role_id)

        scheduled_event = None
        try:
            scheduled_event = await interaction.guild.fetch_scheduled_event(event_id)
        except discord.NotFound:
            scheduled_event = None

        if not scheduled_event:
            if channel:
                await channel.delete(reason='schedule fix cleanup')
            if role:
                await role.delete(reason='schedule fix cleanup')
            db.delete_event(event_id)
            cleaned += 1
            continue


        updated_channel_id = channel_id
        updated_role_id = role_id

        if not role:
            role = await interaction.guild.create_role(
                name=_format_event_date(scheduled_event.start_time)
            )
            updated_role_id = role.id

        if not channel:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                role: discord.PermissionOverwrite(view_channel=True),
            }
            target_category = interaction.guild.get_channel(UPCOMING_CATEGORY_ID)
            if scheduled_event.status == discord.EventStatus.completed:
                target_category = interaction.guild.get_channel(ENDED_CATEGORY_ID)
            channel = await interaction.guild.create_text_channel(
                f"{_format_event_date(scheduled_event.start_time)}_飲み会",
                overwrites=overwrites,
                category=target_category,
            )
            updated_channel_id = channel.id
        else:
            target_category_id = UPCOMING_CATEGORY_ID
            if scheduled_event.status == discord.EventStatus.completed:
                target_category_id = ENDED_CATEGORY_ID
            if channel.category_id != target_category_id:
                target_category = interaction.guild.get_channel(target_category_id)
                await channel.edit(category=target_category)

        if updated_channel_id != channel_id or updated_role_id != role_id:
            db.update_event(event_id, updated_channel_id, updated_role_id)
            fixed += 1

    await interaction.response.send_message(
        f'修復完了: 修復 {fixed} 件 / 削除 {cleaned} 件',
        ephemeral=True,
    )


tree.add_command(schedule_group)


if __name__ == '__main__':
    client.run(TOKEN)
