import discord
from discord import app_commands

from ._log import log_command


def _format_event_date(dt):
    return dt.strftime('%Y-%m-%d')


def register(schedule_group: app_commands.Group, db, upcoming_category_id: int, ended_category_id: int) -> None:
    @schedule_group.command(name='fix', description='不整合を検出して修復')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def schedule_fix(interaction: discord.Interaction):
        log_command('schedule.fix', interaction.guild_id, interaction.user.id)
        if not interaction.guild:
            await interaction.response.send_message('サーバー内で実行してください。', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        records = db.list_events()
        if not records:
            await interaction.followup.send('登録済みスケジュールはありません。', ephemeral=True)
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
                target_category = interaction.guild.get_channel(upcoming_category_id)
                if scheduled_event.status == discord.EventStatus.completed:
                    target_category = interaction.guild.get_channel(ended_category_id)
                channel = await interaction.guild.create_text_channel(
                    f"{_format_event_date(scheduled_event.start_time)}_飲み会",
                    overwrites=overwrites,
                    category=target_category,
                )
                updated_channel_id = channel.id
            else:
                target_category_id = upcoming_category_id
                if scheduled_event.status == discord.EventStatus.completed:
                    target_category_id = ended_category_id
                if channel.category_id != target_category_id:
                    target_category = interaction.guild.get_channel(target_category_id)
                    await channel.edit(category=target_category)

            if updated_channel_id != channel_id or updated_role_id != role_id:
                db.update_event(event_id, updated_channel_id, updated_role_id)
                fixed += 1

        await interaction.followup.send(
            f'修復完了: 修復 {fixed} 件 / 削除 {cleaned} 件',
            ephemeral=True,
        )
