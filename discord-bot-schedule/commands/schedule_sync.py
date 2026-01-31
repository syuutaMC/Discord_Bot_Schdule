import discord
from discord import app_commands
from zoneinfo import ZoneInfo

from ._log import log_command


def _format_event_date(dt) -> str:
    return dt.astimezone(ZoneInfo("Asia/Tokyo")).strftime('%Y-%m-%d')


def register(schedule_group: app_commands.Group, db, upcoming_category_id: int) -> None:
    @schedule_group.command(name='sync', description='Bot停止中のイベントを手動で同期')
    @app_commands.checks.has_permissions(manage_guild=True)
    async def schedule_sync(interaction: discord.Interaction):
        log_command('schedule.sync', interaction.guild_id, interaction.user.id)
        if not interaction.guild:
            await interaction.response.send_message('サーバー内で実行してください。', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        created = 0
        updated = 0
        skipped = 0

        try:
            events = await interaction.guild.fetch_scheduled_events()
        except discord.HTTPException:
            await interaction.followup.send('イベント一覧の取得に失敗しました。', ephemeral=True)
            return

        for event in events:
            if event.status != discord.EventStatus.scheduled:
                skipped += 1
                continue

            record = db.get_event(event.id)
            role_id = record[2] if record else None
            channel_id = record[1] if record else None

            role = interaction.guild.get_role(role_id) if role_id else None
            if not role:
                role_name = _format_event_date(event.start_time)
                role = discord.utils.get(interaction.guild.roles, name=role_name)
                if not role:
                    role = await interaction.guild.create_role(name=role_name)

            channel = interaction.guild.get_channel(channel_id) if channel_id else None
            if not channel:
                channel_name = f"{_format_event_date(event.start_time)}_飲み会"
                channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)

                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    role: discord.PermissionOverwrite(view_channel=True),
                }
                upcoming_category = interaction.guild.get_channel(upcoming_category_id)
                if channel is None:
                    channel = await interaction.guild.create_text_channel(
                        channel_name,
                        overwrites=overwrites,
                        category=upcoming_category,
                    )
                    created += 1
                else:
                    await channel.edit(overwrites=overwrites, category=upcoming_category)

            if record:
                if role_id != role.id or channel_id != channel.id:
                    db.update_event(event.id, channel.id, role.id)
                    updated += 1
            else:
                db.insert_event(event.id, channel.id, role.id)
                created += 1

            try:
                async for attendee in event.users():
                    member = None
                    if isinstance(attendee, discord.Member):
                        member = attendee
                    elif isinstance(attendee, discord.User):
                        member = interaction.guild.get_member(attendee.id)
                        if member is None:
                            try:
                                member = await interaction.guild.fetch_member(attendee.id)
                            except discord.HTTPException:
                                member = None
                    if member and role not in member.roles:
                        await member.add_roles(role)
            except discord.HTTPException:
                continue

        await interaction.followup.send(
            f'同期完了: 作成 {created} / 更新 {updated} / スキップ {skipped}',
            ephemeral=True,
        )