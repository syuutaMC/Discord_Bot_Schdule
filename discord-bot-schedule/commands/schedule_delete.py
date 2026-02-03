import discord
from discord import app_commands

from ._log import log_command


def register(schedule_group: app_commands.Group, db) -> None:
    @schedule_group.command(name='delete', description='指定したスケジュールを削除（DB/チャンネル/ロール）')
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(event_id='DiscordスケジュールイベントのID')
    async def schedule_delete(interaction: discord.Interaction, event_id: str):
        log_command('schedule.delete', interaction.guild_id, interaction.user.id)
        if not interaction.guild:
            await interaction.response.send_message('サーバー内で実行してください。', ephemeral=True)
            return

        try:
            event_id_int = int(event_id.strip())
        except ValueError:
            await interaction.response.send_message('event_id は整数で入力してください。', ephemeral=True)
            return

        record = db.get_event(event_id_int)
        if not record:
            await interaction.response.send_message('該当のレコードが見つかりません。', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        _, channel_id, role_id = record
        channel = interaction.guild.get_channel(channel_id)
        role = interaction.guild.get_role(role_id)

        # Delete scheduled event
        try:
            scheduled_event = await interaction.guild.fetch_scheduled_event(event_id_int)
            await scheduled_event.delete()
        except discord.NotFound:
            pass  # Already deleted
        except discord.HTTPException as e:
            print(f"Failed to delete event {event_id_int}: {e}")

        if channel:
            try:
                await channel.delete(reason='schedule delete command')
            except discord.NotFound:
                pass  # Already deleted
        if role:
            try:
                await role.delete(reason='schedule delete command')
            except discord.NotFound:
                pass  # Already deleted

        db.delete_event(event_id_int)
        await interaction.followup.send('削除しました。', ephemeral=True)
