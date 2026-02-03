import discord
from discord import app_commands

from ._log import log_command


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


def register(schedule_group: app_commands.Group, db) -> None:
    @schedule_group.command(name='list', description='DBに保存されているスケジュール一覧を表示')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def schedule_list(interaction: discord.Interaction):
        log_command('schedule.list', interaction.guild_id, interaction.user.id)
        if not interaction.guild:
            await interaction.response.send_message('サーバー内で実行してください。', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        events = db.list_events()
        if not events:
            await interaction.followup.send('登録済みスケジュールはありません。', ephemeral=True)
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
        await interaction.followup.send(chunks[0], ephemeral=True)
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk, ephemeral=True)
