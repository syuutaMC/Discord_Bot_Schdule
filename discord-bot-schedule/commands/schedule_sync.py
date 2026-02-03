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

            record_before = db.get_event(event.id)
            # Import sync function from main
            from main import _sync_scheduled_event
            await _sync_scheduled_event(interaction.guild, event)
            record_after = db.get_event(event.id)

            if not record_before:
                created += 1
            elif record_before[1:] != record_after[1:]:
                updated += 1

        await interaction.followup.send(
            f'同期完了: 作成 {created} / 更新 {updated} / スキップ {skipped}',
            ephemeral=True,
        )