import discord
from discord import app_commands

from ._log import log_command


def register(schedule_group: app_commands.Group, db) -> None:
    @schedule_group.command(name='info', description='指定したスケジュールの詳細を表示')
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(event_id='DiscordスケジュールイベントのID')
    async def schedule_info(interaction: discord.Interaction, event_id: int):
        log_command('schedule.info', interaction.guild_id, interaction.user.id)
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
